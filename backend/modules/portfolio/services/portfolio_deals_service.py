from backend.common.consts import SQLServerConsts, MessageConsts
from backend.common.responses.exceptions import BaseExceptionResponse
from backend.modules.base.query_builder import TextSQL
from backend.modules.portfolio.entities import Deals
from backend.modules.portfolio.repositories import AccountsRepo, DealsRepo
from backend.modules.portfolio.utils.deals_utils import DealsUtils
from backend.modules.dnse.trading_session import TradingSession
from backend.utils.logger import LOGGER
from backend.utils.time_utils import TimeUtils


LOGGER_PREFIX = "[DealsService]"


class DealsService:
    repo = DealsRepo
    accounts_repo = AccountsRepo

    @classmethod
    async def update_newest_deals_daily(cls) -> bool:
        """Update deals for all accounts"""
        try:
            existing_accounts = await cls.accounts_repo.get_all()
            existing_accounts = [
                account
                for account in existing_accounts
                if account.get("accountType") == "0449"
            ]

            if len(existing_accounts) == 0:
                LOGGER.warning(f"{LOGGER_PREFIX} No account found")
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
                        return False

                    async with session.users_client() as users_client:
                        deals_raw = await users_client.get_account_deals(account_no=broker_account_id)

                        if not deals_raw:
                            continue

                        if len(deals_raw["deals"]) == 0:
                            continue

                        # Prepare deals data
                        current_time = TimeUtils.get_current_vn_time()
                        today_str = current_time.strftime(SQLServerConsts.DATE_FORMAT)

                        deals_list = [
                            DealsUtils.extract_deal_data(raw_data=deal, date=today_str)
                            for deal in deals_raw["deals"]
                        ]
                        if not deals_list:
                            continue

                        data.extend(deals_list)

            with cls.repo.session_scope() as session:
                if data:
                    # Upsert deals
                    await cls.repo.upsert(
                        temp_table=f"#{cls.repo.query_builder.table}",
                        records=data,
                        identity_columns=[Deals.brokerAccountId.name, Deals.date.name],
                        text_clauses={
                            "__updatedAt__": TextSQL(
                                SQLServerConsts.GMT_7_NOW_VARCHAR
                            )
                        },
                    )
                    session.commit()
                    LOGGER.info(f"{LOGGER_PREFIX} Deals updated successfully for {len(data)} accounts")
                else:
                    LOGGER.warning(f"{LOGGER_PREFIX} No deals data to update")

            return {"success": True}



        except Exception as e:
            raise BaseExceptionResponse(
                http_code=500,
                status_code=500,
                message=MessageConsts.INTERNAL_SERVER_ERROR,
                errors=str(e),
            )