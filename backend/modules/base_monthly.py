import datetime
import pandas as pd
import numpy as np
from abc import abstractmethod
from typing import Dict
import time
from dateutil.relativedelta import relativedelta

from backend.common.consts import SQLServerConsts
from backend.modules.base.repositories import BaseRepo
from backend.modules.portfolio.entities import ProcessTracking
from backend.modules.portfolio.repositories import ProcessTrackingRepo
from backend.modules.base.query_builder import TextSQL

class BaseMonthlyService:
    repo: BaseRepo
    process_tracking_repo = ProcessTrackingRepo

    @classmethod
    async def update_newest_data_all_monthly(cls) -> bool:
        with cls.repo.session_scope() as session:
            conditions = {
                ProcessTracking.schemaName.name: cls.repo.query_builder.schema,
                ProcessTracking.tableName.name: cls.repo.query_builder.table,
                ProcessTracking.keyName.name: "lastTradingDay",
            }
            tracking_records = await cls.process_tracking_repo.get_by_condition(conditions=conditions)
            if len(tracking_records) == 0:
                tracking_records = await cls.process_tracking_repo.insert_many(records=[conditions], returning=True)
                session.commit()
            if len(tracking_records) > 1:
                raise Exception(f"duplicate tracking records {[t[ProcessTracking.id.name] for t in tracking_records]}")
            tracking_record = tracking_records[0]
            key_val = tracking_record[ProcessTracking.keyValue.name]
            if key_val is not None:
                continue_trading_day = key_val
            else:
                continue_trading_day = SQLServerConsts.START_TRADING_MONTH
            await cls.update_newest_data_from_month_year(from_month_year=continue_trading_day, process_tracking=tracking_record)
            print("DONE")
            time.sleep(3)
        return True

    @classmethod
    @abstractmethod
    async def update_newest_data_from_month_year(cls, from_month_year: str, process_tracking: Dict):
        from_date = datetime.datetime.strptime(from_month_year, '%Y-%m')
        from_date_ = (from_date - relativedelta(months=15)).strftime(SQLServerConsts.DATE_FORMAT)
        from_date_str = from_date.strftime(SQLServerConsts.DATE_FORMAT)
        data = cls.update_data(from_date=from_date_)
        data = data[data['date'] >= from_date_str].reset_index(drop=True)
        last_date = data['date'].iloc[-1]
        last_key_value = last_date[:7]
        data = data.drop(columns=['date'], errors='ignore')
        data.to_csv("universe_top20.csv", index=False)

        with cls.repo.session_scope() as session:
            temp_table = f"#{cls.repo.query_builder.table}"
            await cls.repo.upsert(
                temp_table=temp_table,
                records=data,
                identity_columns=["symbol", "year", "month"],
                text_clauses={"__updatedAt__": TextSQL(SQLServerConsts.GMT_7_NOW_VARCHAR)},
            )
            await cls.process_tracking_repo.update(
                record={
                    ProcessTracking.id.name: process_tracking[ProcessTracking.id.name],
                    ProcessTracking.keyValue.name: last_key_value,
                },
                identity_columns=[ProcessTracking.id.name],
                returning=False,
                text_clauses={"updatedAt": TextSQL(SQLServerConsts.GMT_7_NOW_VARCHAR)},
            )
            session.commit()

    @classmethod
    @abstractmethod
    def update_data(cls, from_date) -> pd.DataFrame:
        pass
