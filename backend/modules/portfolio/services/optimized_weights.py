import pandas as pd
import numpy as np

from backend.common.consts import SQLServerConsts
from backend.common.responses.exceptions import BaseExceptionResponse
from backend.db.sessions import mart_session_scope
from backend.modules.base_daily import BaseDailyService
from backend.modules.portfolio.entities import UniverseTopMonthly, OptimizedWeights
from backend.modules.portfolio.repositories import (
    OptimizedWeightsRepo,
    UniverseTopMonthlyRepo,
)
from backend.modules.portfolio.core import PortfolioOptimizer
from backend.common.consts import MessageConsts
from backend.utils.time_utils import TimeUtils


class OptimizedWeightsService(BaseDailyService):
    repo = OptimizedWeightsRepo

    @classmethod
    async def update_data(cls, from_date) -> pd.DataFrame:
        from_date_ = pd.to_datetime(from_date)
        time_range = 21

        # Get price data for the last 21 days
        with mart_session_scope() as mart_session:
            sql_query = f"""
                SET TRANSACTION ISOLATION LEVEL READ UNCOMMITTED;

                WITH UncommittedData AS (
                SELECT 
                    [ticker] 
                    ,[date] 
                    ,[closePriceAdjusted]
                    ,ROW_NUMBER() OVER (PARTITION BY [ticker], [date] ORDER BY __updatedAt__ DESC) AS rn
                FROM [priceVolume].[priceVolume]
                )

                SELECT * FROM UncommittedData
                where rn = 1 and [date] >= '{from_date}'
                ORDER BY [date], [ticker];
            """
            conn = mart_session.connection().connection
            df_stock = pd.read_sql_query(sql_query, conn)
            df_stock_pivoted = df_stock.pivot(
                index="date", columns="ticker", values="closePriceAdjusted"
            )

        T = df_stock_pivoted.shape[0]
        tmp_year = from_date_.year
        tmp_month = from_date_.month
        assets = []
        optimized_weights = []
        for i in range(time_range - 1, T):
            window = df_stock_pivoted.iloc[i - time_range + 1 : i + 1]
            end_of_period = window.index[-1]  # Use index instead of column 'date'

            # Check if need to update the assets for the current month
            if (
                pd.to_datetime(end_of_period).year != tmp_year
                or pd.to_datetime(end_of_period).month != tmp_month
                or not assets
            ):
                tmp_year = pd.to_datetime(end_of_period).year
                tmp_month = pd.to_datetime(end_of_period).month

                records = await UniverseTopMonthlyRepo.get_asset_by_year_month(
                    year=tmp_year, month=tmp_month
                )
                assets = [record[UniverseTopMonthly.symbol.name] for record in records]

            # Filter columns (tickers) that are in the current month's universe
            available_assets = [asset for asset in assets if asset in window.columns]
            df_portfolio = window[available_assets].copy()
            x_CEMV, x_CEMV_neutralized, x_CEMV_limited, x_CEMV_neutralized_limit = PortfolioOptimizer.optimize(df_portfolio=df_portfolio)

            date = pd.to_datetime(end_of_period)
            for j in range(len(x_CEMV)):
                record = {
                    OptimizedWeights.date.name: date.strftime(SQLServerConsts.DATE_FORMAT),
                    OptimizedWeights.symbol.name: df_portfolio.columns[j],
                    OptimizedWeights.initialWeight.name: x_CEMV[j],
                    OptimizedWeights.neutralizedWeight.name: x_CEMV_neutralized[j],
                    OptimizedWeights.limitedWeight.name: x_CEMV_limited[j],
                    OptimizedWeights.neutralizedLimitedWeight.name: x_CEMV_neutralized_limit[j],
                    OptimizedWeights.algorithm.name: "CEMV",
                }
                optimized_weights.append(record)

        optimized_weights_df = pd.DataFrame(optimized_weights)
        return optimized_weights_df
