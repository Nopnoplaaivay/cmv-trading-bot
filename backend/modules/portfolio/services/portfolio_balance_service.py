from typing import List, Optional, Dict, Any
from decimal import Decimal
from datetime import datetime

from backend.common.consts import SQLServerConsts, MessageConsts
from backend.common.responses.exceptions import BaseExceptionResponse
from backend.modules.base.query_builder import TextSQL
from backend.modules.portfolio.entities import Balances
from backend.modules.portfolio.repositories import AccountsRepo, BalancesRepo
from backend.modules.portfolio.utils.balance_utils import BalanceUtils
from backend.modules.dnse.trading_session import TradingSession
from backend.utils.logger import LOGGER
from backend.utils.time_utils import TimeUtils


LOGGER_PREFIX = "[BalanceService]"


class BalanceService:
    repo = BalancesRepo
    accounts_repo = AccountsRepo

    @classmethod
    async def update_newest_balances_daily(cls) -> bool:
        try:

            existing_accounts = await cls.accounts_repo.get_all()
            existing_accounts = [
                account
                for account in existing_accounts
                if account.get("accountType") == "0449"
            ]

            if len(existing_accounts) == 0:
                LOGGER.warning(f"No account found")
                return False


            data = []
            for account in existing_accounts:
                custody_code = account.get("custodyCode")
                password = account.get("password")
                broker_account_id = account.get("brokerAccountId")

                # Get current balance from DNSE API
                async with TradingSession(account=custody_code) as session:
                    if not await session.authenticate(password=password):
                        LOGGER.error(f"{LOGGER_PREFIX} Authentication failed for account {custody_code}")
                        raise BaseExceptionResponse(
                            http_code=404,
                            status_code=404,
                            message=MessageConsts.VALIDATION_FAILED,
                            errors=str(e),
                        )
                    
                    async with session.users_client() as users_client:
                        balance_dict = await users_client.get_account_balance(account_no=broker_account_id)

                        if not balance_dict:
                            LOGGER.warning(f"{LOGGER_PREFIX} No balance data found for account {broker_account_id}")
                            continue

                        # Prepare balance data
                        current_time = TimeUtils.get_current_vn_time()
                        today_str = current_time.strftime(SQLServerConsts.DATE_FORMAT)
                        balance_data = BalanceUtils.extract_balance_data(
                            raw_data=balance_dict, date=today_str
                        )
                        data.append(balance_data)


            with cls.repo.session_scope() as session:
                if data:
                    # Upsert balances
                    await cls.repo.upsert(
                        temp_table=f"#{cls.repo.query_builder.table}",
                        records=data,
                        identity_columns=[Balances.brokerAccountId.name, Balances.date.name],
                        text_clauses={
                            "__updatedAt__": TextSQL(
                                SQLServerConsts.GMT_7_NOW_VARCHAR
                            )
                        },
                    )
                    session.commit()
                    LOGGER.info(f"{LOGGER_PREFIX} Balances updated successfully for {len(data)} accounts")
                else:
                    LOGGER.warning(f"{LOGGER_PREFIX} No balance data to update")

            return {"success": True}


        except Exception as e:
            raise BaseExceptionResponse(
                http_code=500,
                status_code=500,
                message=MessageConsts.INTERNAL_SERVER_ERROR,
                errors=str(e),
            )
