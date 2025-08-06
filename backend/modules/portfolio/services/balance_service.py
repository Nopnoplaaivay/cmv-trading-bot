from typing import List, Optional, Dict, Any
from decimal import Decimal
from datetime import datetime

from backend.common.consts import SQLServerConsts
from backend.modules.base.query_builder import TextSQL
from backend.modules.portfolio.entities import Balances
from backend.modules.portfolio.repositories import AccountsRepo, BalancesRepo
from backend.modules.portfolio.utils.balance_utils import BalanceUtils
from backend.modules.dnse.trading_session import TradingSession
from backend.utils.logger import LOGGER
from backend.utils.time_utils import TimeUtils


class BalanceService:
    repo = BalancesRepo
    accounts_repo = AccountsRepo

    @classmethod
    async def update_newest_balances_daily(cls) -> bool:
        """Update balance for a all account"""
        try:
            LOGGER.info(f"Updating balance for all accounts")

            # Get account details
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
                        LOGGER.error(f"Authentication failed for account {custody_code}")
                        return False

                    async with session.users_client() as users_client:
                        balance_dict = await users_client.get_account_balance(account_no=broker_account_id)

                        if not balance_dict:
                            LOGGER.warning(f"No balance data found for account {broker_account_id}")
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
                    LOGGER.info(f"Balances updated successfully for {len(data)} accounts")
                else:
                    LOGGER.warning("No balance data to update")

            return {"success": True}


        except Exception as e:
            LOGGER.error(f"Error updating balance for accounts: {e}")
            return False

    # @classmethod
    # async def update_newest_data_all_daily(cls) -> Dict[str, Any]:
    #     """Update balance data for all active accounts"""
    #     try:
    #         LOGGER.info("Starting daily balance update for all accounts")

    #         # Get all active accounts
    #         users_repo = UsersRepo
    #         with users_repo.session_scope() as session:
    #             active_users = await users_repo.get_by_condition(
    #                 {Users.isActive.name: True}
    #             )

    #         if not active_users:
    #             LOGGER.warning("No active users found")
    #             return {
    #                 "success": False,
    #                 "message": "No active users found",
    #                 "updated_accounts": 0,
    #                 "failed_accounts": 0,
    #             }

    #         # Get all accounts for active users
    #         all_accounts = []
    #         for user in active_users:
    #             user_id = user.get(Users.id.name)
    #             accounts = await cls.accounts_repo.get_by_condition(
    #                 {Accounts.userId.name: user_id}
    #             )
    #             all_accounts.extend(accounts)

    #         if not all_accounts:
    #             LOGGER.warning("No accounts found for active users")
    #             return {
    #                 "success": False,
    #                 "message": "No accounts found for active users",
    #                 "updated_accounts": 0,
    #                 "failed_accounts": 0,
    #             }

    #         # Update balance for each account
    #         updated_count = 0
    #         failed_count = 0

    #         for account in all_accounts:
    #             account_id = account.get(Accounts.id.name)
    #             broker_account_id = account.get(Accounts.brokerAccountId.name)

    #             try:
    #                 success = await cls.update_account_balance(
    #                     account_id, broker_account_id
    #                 )
    #                 if success:
    #                     updated_count += 1
    #                 else:
    #                     failed_count += 1

    #             except Exception as e:
    #                 LOGGER.error(f"Error updating account {broker_account_id}: {e}")
    #                 failed_count += 1

    #         # Summary
    #         total_accounts = len(all_accounts)
    #         success_rate = (
    #             (updated_count / total_accounts * 100) if total_accounts > 0 else 0
    #         )

    #         result = {
    #             "success": updated_count > 0,
    #             "message": f"Balance update completed: {updated_count}/{total_accounts} accounts updated",
    #             "updated_accounts": updated_count,
    #             "failed_accounts": failed_count,
    #             "total_accounts": total_accounts,
    #             "success_rate": round(success_rate, 2),
    #         }

    #         LOGGER.info(f"Daily balance update completed: {result}")

    #         # Send notification if there are failures
    #         if failed_count > 0:
    #             await notify_error(
    #                 "BALANCE UPDATE WARNING",
    #                 f"Balance update completed with {failed_count} failures out of {total_accounts} accounts",
    #             )

    #         return result

    #     except Exception as e:
    #         LOGGER.error(f"Error in daily balance update: {e}")
    #         await notify_error(
    #             "BALANCE UPDATE ERROR", f"Daily balance update failed: {str(e)}"
    #         )
    #         return {
    #             "success": False,
    #             "message": f"Daily balance update failed: {str(e)}",
    #             "updated_accounts": 0,
    #             "failed_accounts": 0,
    #         }

    # @classmethod
    # async def get_latest_balance(cls, account_id: str) -> Optional[Dict[str, Any]]:
    #     """Get the latest balance for an account"""
    #     try:
    #         balances = await cls.balances_repo.get_by_condition(
    #             {Balances.accountId.name: account_id}
    #         )

    #         if not balances:
    #             return None

    #         # Sort by balance date descending to get the latest
    #         latest_balance = max(
    #             balances, key=lambda x: x.get(Balances.balanceDate.name, "")
    #         )
    #         return latest_balance

    #     except Exception as e:
    #         LOGGER.error(f"Error getting latest balance for account {account_id}: {e}")
    #         return None
