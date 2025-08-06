import uuid
from typing import Dict, Optional

from backend.common.consts import MessageConsts, SQLServerConsts
from backend.common.responses.exceptions.base_exceptions import BaseExceptionResponse
from backend.modules.auth.types import JwtPayload
from backend.modules.base.query_builder import TextSQL
from backend.modules.dnse.trading_api.users_client import UsersClient
from backend.modules.dnse.trading_session import TradingSession
from backend.modules.auth.entities import Users
from backend.modules.auth.repositories import UsersRepo
from backend.modules.portfolio.dtos import SetupDNSEAccountDTO
from backend.modules.portfolio.entities import Accounts, Balances, Deals
from backend.modules.portfolio.repositories import (
    AccountsRepo,
    BalancesRepo,
    DealsRepo,
)
from backend.utils.logger import LOGGER


class AccountsService:
    repo = AccountsRepo

    @classmethod
    async def setup_dnse_account(cls, user: JwtPayload, payload: SetupDNSEAccountDTO):
        try:

            existing_account = await cls.repo.get_accounts_by_username(payload.username)
            if existing_account:
                for account in existing_account:
                    if account[Accounts.userId.name] != user.userId:
                        raise BaseExceptionResponse(
                            http_code=409,
                            status_code=409,
                            message=MessageConsts.CONFLICT,
                            errors="This broker account ID is already registered to another user",
                        )

            username = payload.username
            password = payload.password

            async with TradingSession(account=username) as session:
                if not await session.authenticate(password=password):
                    raise BaseExceptionResponse(
                        http_code=401,
                        status_code=401,
                        message=MessageConsts.UNAUTHORIZED,
                        errors="Authentication failed",
                    )
                LOGGER.info(
                    f"User {user.userId} authenticated successfully with DNSE account {username}"
                )

                if session.is_jwt_authenticated():
                    async with session.users_client() as users_client:
                        user_dict = await users_client.get_users_info()
                        accounts_dict = await users_client.get_user_accounts()

                        if not user_dict or not accounts_dict:
                            raise BaseExceptionResponse(
                                http_code=502,
                                status_code=502,
                                message=MessageConsts.TRADING_API_ERROR,
                                errors="Failed to fetch user or account information from DNSE API",
                            )

                        user_data = {
                            Users.id.name: user.userId,
                            Users.mobile.name: user_dict.get("mobile"),
                            Users.email.name: user_dict.get("email"),
                        }

                        accounts_data = []
                        accounts = accounts_dict.get("accounts", [])
                        for account in accounts:
                            accounts_data.append(
                                {
                                    Accounts.userId.name: user.userId,
                                    Accounts.name.name: account.get("name"),
                                    Accounts.accountType.name: account.get(
                                        "accountType"
                                    ),
                                    Accounts.identificationCode.name: user_dict.get(
                                        "identificationCode"
                                    ),
                                    Accounts.custodyCode.name: account.get(
                                        "custodyCode"
                                    ),
                                    Accounts.password.name: payload.password,
                                    Accounts.brokerName.name: "DNSE",
                                    Accounts.brokerAccountId.name: account.get("id"),
                                    Accounts.brokerInvestorId.name: account.get(
                                        "investorId"
                                    ),
                                }
                            )

                        with UsersRepo.session_scope() as user_repo_session:
                            await UsersRepo.update(
                                record={
                                    Users.id.name: user.userId,
                                    Users.mobile.name: user_data.get("mobile"),
                                    Users.email.name: user_data.get("email"),
                                },
                                identity_columns=[Users.id.name],
                                returning=False,
                                text_clauses={
                                    "__updatedAt__": TextSQL(
                                        SQLServerConsts.GMT_7_NOW_VARCHAR
                                    )
                                },
                            )
                            user_repo_session.commit()

                        # Upsert accounts
                        with cls.repo.session_scope() as account_repo_session:
                            temp_table = f"#{cls.repo.query_builder.table}"
                            await cls.repo.upsert(
                                temp_table=temp_table,
                                records=accounts_data,
                                identity_columns=["custodyCode", "brokerAccountId"],
                                text_clauses={
                                    "__updatedAt__": TextSQL(
                                        SQLServerConsts.GMT_7_NOW_VARCHAR
                                    )
                                },
                            )
                            account_repo_session.commit()

                        # Upsert balances, deals for each account
                        for account in accounts_data:
                            broker_account_id = account[Accounts.brokerAccountId.name]

                            balance_dict = await users_client.get_account_balance(
                                account_no=broker_account_id
                            )

                            if not balance_dict:
                                raise BaseExceptionResponse(
                                    http_code=502,
                                    status_code=502,
                                    message=MessageConsts.TRADING_API_ERROR,
                                    errors="Failed to fetch balance from DNSE API",
                                )

                            balance_data = cls.extract_balance_data(
                                raw_data=balance_dict
                            )

                            with BalancesRepo.session_scope() as balance_repo_session:
                                temp_table = f"#{BalancesRepo.query_builder.table}"
                                await BalancesRepo.upsert(
                                    temp_table=temp_table,
                                    records=[balance_data],
                                    identity_columns=[Balances.brokerAccountId.name],
                                    text_clauses={
                                        "__updatedAt__": TextSQL(
                                            SQLServerConsts.GMT_7_NOW_VARCHAR
                                        )
                                    },
                                )
                                balance_repo_session.commit()

                            # Upsert deals
                            deals_raw = await users_client.get_account_deals(
                                account_no=broker_account_id
                            )
                            if not deals_raw:
                                raise BaseExceptionResponse(
                                    http_code=502,
                                    status_code=502,
                                    message=MessageConsts.TRADING_API_ERROR,
                                    errors="Failed to fetch deals from DNSE API",
                                )
                            deals_data = [
                                cls.extract_deal_data(raw_data=deal)
                                for deal in deals_raw["deals"]
                            ]
                            print(f"Deals data: {deals_data}")
                            with DealsRepo.session_scope() as deals_repo_session:
                                temp_table = f"#{DealsRepo.query_builder.table}"
                                await DealsRepo.upsert(
                                    temp_table=temp_table,
                                    records=deals_data,
                                    identity_columns=[Deals.dealId.name],
                                    text_clauses={
                                        "__updatedAt__": TextSQL(
                                            SQLServerConsts.GMT_7_NOW_VARCHAR
                                        )
                                    },
                                )
                                deals_repo_session.commit()

            return {
                "message": "DNSE account setup successfully",
            }

        except BaseExceptionResponse:
            raise
        except Exception as e:
            LOGGER.error(f"Failed to setup DNSE account for user {user.userId}: {e}")
            raise BaseExceptionResponse(
                http_code=500,
                status_code=500,
                message=MessageConsts.INTERNAL_SERVER_ERROR,
                errors=str(e),
            )

    @classmethod
    def extract_balance_data(cls, raw_data: Dict) -> Dict:
        field_mapping = {
            Balances.brokerAccountId.name: raw_data.get("investorAccountId"),
            Balances.totalCash.name: raw_data.get("totalCash"),
            Balances.availableCash.name: raw_data.get("availableCash"),
            Balances.termDeposit.name: raw_data.get("termDeposit"),
            Balances.depositInterest.name: raw_data.get("depositInterest"),
            Balances.stockValue.name: raw_data.get("stockValue"),
            Balances.marginableAmount.name: raw_data.get("marginableAmount"),
            Balances.nonMarginableAmount.name: raw_data.get("nonMarginableAmount"),
            Balances.totalDebt.name: raw_data.get("totalDebt"),
            Balances.netAssetValue.name: raw_data.get("netAssetValue"),
            Balances.receivingAmount.name: raw_data.get("receivingAmount"),
            Balances.secureAmount.name: raw_data.get("secureAmount"),
            Balances.depositFeeAmount.name: raw_data.get("depositFeeAmount"),
            Balances.maxLoanLimit.name: raw_data.get("maxLoanLimit"),
            Balances.withdrawableCash.name: raw_data.get("withdrawableCash"),
            Balances.collateralValue.name: raw_data.get("collateralValue"),
            Balances.orderSecured.name: raw_data.get("orderSecured"),
            Balances.purchasingPower.name: raw_data.get("purchasingPower"),
            Balances.cashDividendReceiving.name: raw_data.get("cashDividendReceiving"),
            Balances.marginDebt.name: raw_data.get("marginDebt"),
            Balances.marginRate.name: raw_data.get("marginRate"),
            Balances.ppWithdraw.name: raw_data.get("ppWithdraw"),
            Balances.blockMoney.name: raw_data.get("blockMoney"),
            Balances.totalRemainDebt.name: raw_data.get("totalRemainDebt"),
            Balances.totalUnrealizedDebt.name: raw_data.get("totalUnrealizedDebt"),
            Balances.blockedAmount.name: raw_data.get("blockedAmount"),
            Balances.advancedAmount.name: raw_data.get("advancedAmount"),
            Balances.advanceWithdrawnAmount.name: raw_data.get(
                "advanceWithdrawnAmount"
            ),
        }

        return {k: v for k, v in field_mapping.items() if v is not None}

    @classmethod
    def extract_deal_data(cls, raw_data: Dict) -> Dict:
        field_mapping = {
            Deals.brokerAccountId.name: raw_data.get("accountNo"),
            Deals.dealId.name: raw_data.get("id"),
            Deals.symbol.name: raw_data.get("symbol"),
            Deals.status.name: raw_data.get("status"),
            Deals.side.name: raw_data.get("side"),
            Deals.secure.name: raw_data.get("secure"),
            Deals.accumulateQuantity.name: raw_data.get("accumulateQuantity"),
            Deals.tradeQuantity.name: raw_data.get("tradeQuantity"),
            Deals.closedQuantity.name: raw_data.get("closedQuantity"),
            Deals.t0ReceivingQuantity.name: raw_data.get("t0ReceivingQuantity"),
            Deals.t1ReceivingQuantity.name: raw_data.get("t1ReceivingQuantity"),
            Deals.t2ReceivingQuantity.name: raw_data.get("t2ReceivingQuantity"),
            Deals.costPrice.name: raw_data.get("costPrice"),
            Deals.averageCostPrice.name: raw_data.get("averageCostPrice"),
            Deals.marketPrice.name: raw_data.get("marketPrice"),
            Deals.realizedProfit.name: raw_data.get("realizedProfit"),
            Deals.unrealizedProfit.name: raw_data.get("unrealizedProfit"),
            Deals.breakEvenPrice.name: raw_data.get("breakEvenPrice"),
            Deals.dividendReceivingQuantity.name: raw_data.get("dividendReceivingQuantity"),
            Deals.dividendQuantity.name: raw_data.get("dividendQuantity"),
            Deals.cashReceiving.name: raw_data.get("cashReceiving"),
            Deals.rightReceivingCash.name: raw_data.get("rightReceivingCash"),
            Deals.t0ReceivingCash.name: raw_data.get("t0ReceivingCash"),
            Deals.t1ReceivingCash.name: raw_data.get("t1ReceivingCash"),
            Deals.t2ReceivingCash.name: raw_data.get("t2ReceivingCash"),
            Deals.createdDate.name: raw_data.get("createdDate"),
            Deals.modifiedDate.name: raw_data.get("modifiedDate"),
        }

        return {k: v for k, v in field_mapping.items() if v is not None}