from backend.common.consts import SQLServerConsts
from backend.modules.base.query_builder import TextSQL
from backend.modules.portfolio.entities import Deals
from backend.modules.portfolio.repositories import AccountsRepo, DealsRepo
from backend.modules.portfolio.utils.deals_utils import DealsUtils
from backend.modules.dnse.trading_session import TradingSession
from backend.utils.logger import LOGGER
from backend.utils.time_utils import TimeUtils


class DealsService:
    repo = DealsRepo
    accounts_repo = AccountsRepo

    @classmethod
    async def update_newest_deals_daily(cls) -> bool:
        """Update deals for all accounts"""
        try:
            LOGGER.info(f"Updating deals for all accounts")

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
                        deals_raw = await users_client.get_account_deals(account_no=broker_account_id)

                        if not deals_raw:
                            LOGGER.warning(f"No deals data found for account {broker_account_id}")
                            continue

                        if len(deals_raw["deals"]) == 0:
                            LOGGER.warning(f"No deals data found for account {broker_account_id}")
                            continue

                        # Prepare deals data
                        current_time = TimeUtils.get_current_vn_time()
                        today_str = current_time.strftime(SQLServerConsts.DATE_FORMAT)

                        deals_list = [
                            DealsUtils.extract_deal_data(raw_data=deal, date=today_str)
                            for deal in deals_raw["deals"]
                        ]
                        if not deals_list:
                            LOGGER.warning(f"No deals data found for account {broker_account_id}")
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
                    LOGGER.info(f"Deals updated successfully for {len(data)} accounts")
                else:
                    LOGGER.warning("No deals data to update")

            return {"success": True}



        except Exception as e:
            LOGGER.error(f"Error updating deals for accounts: {e}")
            return False


    # @classmethod
    # async def update_newest_data_all_daily(cls) -> Dict[str, Any]:
    #     """Update deals data for all active accounts"""
    #     try:
    #         LOGGER.info("Starting daily deals update for all accounts")

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

    #         # Update deals for each account
    #         updated_count = 0
    #         failed_count = 0
    #         total_deals = 0

    #         for account in all_accounts:
    #             account_id = account.get(Accounts.id.name)
    #             broker_account_id = account.get(Accounts.brokerAccountId.name)

    #             try:
    #                 success = await cls.update_account_deals(
    #                     account_id, broker_account_id
    #                 )
    #                 if success:
    #                     updated_count += 1
    #                     # Count deals for this account
    #                     today_str = TimeUtils.get_current_vn_time().strftime(
    #                         SQLServerConsts.DATE_FORMAT
    #                     )
    #                     account_deals = await cls.deals_repo.get_by_condition(
    #                         {
    #                             Deals.accountId.name: account_id,
    #                             Deals.dealDate.name: today_str,
    #                         }
    #                     )
    #                     total_deals += len(account_deals) if account_deals else 0
    #                 else:
    #                     failed_count += 1

    #             except Exception as e:
    #                 LOGGER.error(
    #                     f"Error updating deals for account {broker_account_id}: {e}"
    #                 )
    #                 failed_count += 1

    #         # Summary
    #         total_accounts = len(all_accounts)
    #         success_rate = (
    #             (updated_count / total_accounts * 100) if total_accounts > 0 else 0
    #         )

    #         result = {
    #             "success": updated_count > 0,
    #             "message": f"Deals update completed: {updated_count}/{total_accounts} accounts updated",
    #             "updated_accounts": updated_count,
    #             "failed_accounts": failed_count,
    #             "total_accounts": total_accounts,
    #             "total_deals": total_deals,
    #             "success_rate": round(success_rate, 2),
    #         }

    #         LOGGER.info(f"Daily deals update completed: {result}")

    #         # Send notification if there are failures
    #         if failed_count > 0:
    #             await notify_error(
    #                 "DEALS UPDATE WARNING",
    #                 f"Deals update completed with {failed_count} failures out of {total_accounts} accounts",
    #             )

    #         return result

    #     except Exception as e:
    #         LOGGER.error(f"Error in daily deals update: {e}")
    #         await notify_error(
    #             "DEALS UPDATE ERROR", f"Daily deals update failed: {str(e)}"
    #         )
    #         return {
    #             "success": False,
    #             "message": f"Daily deals update failed: {str(e)}",
    #             "updated_accounts": 0,
    #             "failed_accounts": 0,
    #         }

    # @classmethod
    # async def get_latest_deals(
    #     cls, account_id: str, symbol: Optional[str] = None
    # ) -> List[Dict[str, Any]]:
    #     """Get the latest deals for an account, optionally filtered by symbol"""
    #     try:
    #         conditions = {Deals.accountId.name: account_id}

    #         if symbol:
    #             conditions[Deals.symbol.name] = symbol

    #         deals = await cls.deals_repo.get_by_condition(conditions)

    #         if not deals:
    #             return []

    #         # Sort by deal date descending to get the latest
    #         deals.sort(key=lambda x: x.get(Deals.dealDate.name, ""), reverse=True)
    #         return deals

    #     except Exception as e:
    #         LOGGER.error(f"Error getting latest deals for account {account_id}: {e}")
    #         return []

    # @classmethod
    # async def get_portfolio_positions(
    #     cls, account_id: str, deal_date: Optional[str] = None
    # ) -> List[Dict[str, Any]]:
    #     """Get current portfolio positions from deals data"""
    #     try:
    #         if not deal_date:
    #             deal_date = TimeUtils.get_current_vn_time().strftime(
    #                 SQLServerConsts.DATE_FORMAT
    #             )

    #         deals = await cls.deals_repo.get_by_condition(
    #             {Deals.accountId.name: account_id, Deals.dealDate.name: deal_date}
    #         )

    #         if not deals:
    #             return []

    #         # Filter only positions with accumulated quantity > 0
    #         positions = []
    #         for deal in deals:
    #             if deal.get(Deals.accumulateQuantity.name, 0) > 0:
    #                 positions.append(deal)

    #         # Sort by unrealized profit descending
    #         positions.sort(
    #             key=lambda x: x.get(Deals.unrealizedProfit.name, 0), reverse=True
    #         )

    #         return positions

    #     except Exception as e:
    #         LOGGER.error(
    #             f"Error getting portfolio positions for account {account_id}: {e}"
    #         )
    #         return []
