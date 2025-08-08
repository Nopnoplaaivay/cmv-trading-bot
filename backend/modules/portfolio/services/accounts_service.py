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
from backend.modules.portfolio.dtos import SetupDNSEAccountDTO, DefaultAccountResponseDTO
from backend.modules.portfolio.entities import Accounts, Balances, Deals
from backend.modules.portfolio.repositories import (
    AccountsRepo,
    BalancesRepo,
    DealsRepo,
)
from backend.modules.portfolio.utils.balance_utils import BalanceUtils
from backend.modules.portfolio.utils.deals_utils import DealsUtils
from backend.utils.logger import LOGGER


class AccountsService:
    repo = AccountsRepo

    @classmethod
    async def get_default_account(cls, user: JwtPayload):
        try:
            accounts = await cls.repo.get_by_user_id(user.userId)
            if not accounts:
                raise BaseExceptionResponse(
                    http_code=404,
                    status_code=404,
                    message=MessageConsts.NOT_FOUND,
                    errors="No accounts found for this user",
                )
            for account in accounts:
                if account[Accounts.accountType.name] == "0449":
                    return DefaultAccountResponseDTO(
                        account_id=account[Accounts.id.name],
                        name=account[Accounts.name.name],
                        broker_name=account[Accounts.brokerName.name],
                        broker_account_id=account[Accounts.brokerAccountId.name],
                        broker_investor_id=account[Accounts.brokerInvestorId.name],
                        is_default=True,
                    ).model_dump()
            return None
        
        except Exception as e:
            LOGGER.error(f"Failed to fetch accounts for user {user.userId}: {e}")
            raise BaseExceptionResponse(
                http_code=500,
                status_code=500,
                message=MessageConsts.INTERNAL_SERVER_ERROR,
                errors=str(e),
            )


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

                            balance_data = BalanceUtils.extract_balance_data(
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
                                DealsUtils.extract_deal_data(raw_data=deal)
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
