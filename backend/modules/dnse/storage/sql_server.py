from typing import Optional, Dict

from backend.common.consts import SQLServerConsts
from backend.common.responses.exceptions import BaseExceptionResponse
from backend.modules.dnse.entities import TradingTokens
from backend.modules.dnse.repositories import TradingTokensRepo
from backend.modules.dnse.storage.base import BaseTokenStorage
from backend.modules.base.query_builder import TextSQL
from backend.utils.logger import LOGGER


class SQLServerTokenStorage(BaseTokenStorage):
    async def save_token(self, token_data: TradingTokens) -> None:
        with TradingTokensRepo.session_scope() as session:
            conditions = {
                TradingTokens.account.name: token_data.account,
                TradingTokens.broker.name: token_data.broker
            }
            existing_tokens = await TradingTokensRepo.get_by_condition(conditions)
            if len(existing_tokens) == 0:
                await TradingTokensRepo.insert(
                    record={
                        TradingTokens.account.name: token_data.account,
                        TradingTokens.jwtToken.name: token_data.jwtToken,
                        TradingTokens.tradingToken.name: token_data.tradingToken,
                        TradingTokens.broker.name: token_data.broker,
                        TradingTokens.jwtCreatedAt.name: token_data.jwtCreatedAt,
                        TradingTokens.tradingCreatedAt.name: token_data.tradingCreatedAt
                    },
                    returning=False
                )
                session.commit()
                return True
            if len(existing_tokens) > 1:
                raise BaseExceptionResponse(
                    http_code=400,
                    status_code=400,
                    message="Duplicate trading tokens found",
                    errors=f"Multiple tokens found: {[t[TradingTokens.id.name] for t in existing_tokens]}"
                )
            existed_token = existing_tokens[0]
            await TradingTokensRepo.update(
                record={
                    TradingTokens.id.name: existed_token[TradingTokens.id.name],
                    TradingTokens.jwtToken.name: token_data.jwtToken,
                    TradingTokens.tradingToken.name: token_data.tradingToken,
                    TradingTokens.broker.name: token_data.broker,
                    TradingTokens.jwtCreatedAt.name: token_data.jwtCreatedAt,
                    TradingTokens.tradingCreatedAt.name: token_data.tradingCreatedAt,
                },
                identity_columns=[TradingTokens.id.name],
                returning=False,
                text_clauses={"updatedAt": TextSQL(SQLServerConsts.GMT_7_NOW_VARCHAR)}
            )
            session.commit()
        LOGGER.info(f"Token for account {token_data.account} saved to SQL Server successfully.")

    async def load_token(self, account: str, broker: str = 'DNSE') -> Optional[TradingTokens]:
        conditions = {
            TradingTokens.account.name: account,
            TradingTokens.broker.name: broker
        }
        existing_tokens = await TradingTokensRepo.get_by_condition(conditions)
        if not existing_tokens:
            return None
        if len(existing_tokens) > 1:
            raise BaseExceptionResponse(
                http_code=400,
                status_code=400,
                message="Duplicate trading tokens found",
                errors=f"Multiple tokens found: {[t[TradingTokens.id.name] for t in existing_tokens]}"
            )
        return TradingTokens.from_dict(data=existing_tokens[0])

    async def delete_token(self, account: str, broker: str = 'DNSE') -> None:
        conditions = {
            TradingTokens.account.name: account,
            TradingTokens.broker.name: broker
        }
        existing_tokens = await TradingTokensRepo.get_by_condition(conditions)
        if not existing_tokens:
            LOGGER.warning(f"No token found for account {account} in broker {broker}.")
            return
        if len(existing_tokens) > 1:
            raise BaseExceptionResponse(
                http_code=400,
                status_code=400,
                message="Duplicate trading tokens found",
                errors=f"Multiple tokens found: {[t[TradingTokens.id.name] for t in existing_tokens]}"
            )
        await TradingTokensRepo.delete(conditions=conditions)
        LOGGER.info(f"Token for account {account} deleted from SQL Server successfully.")

    async def cleanup(self) -> None:
        pass