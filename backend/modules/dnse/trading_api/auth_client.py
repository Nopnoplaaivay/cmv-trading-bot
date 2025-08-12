from typing import Optional
from enum import Enum
import os
from typing import Optional, Dict, Union
from enum import Enum


from backend.common.consts import MessageConsts, SQLServerConsts
from backend.common.configs.dnse import TradingAPIConfig
from backend.common.responses.exceptions.base_exceptions import BaseExceptionResponse
from backend.modules.dnse.entities import TradingTokens
from backend.modules.base_trading_client import BaseTradingClient
from backend.modules.dnse.storage import (
    RedisTokenStorage,
    SQLServerTokenStorage,
    REDIS_AVAILABLE,
)
from backend.utils.logger import LOGGER
from backend.utils.time_utils import TimeUtils


LOGGER_PREFIX = "[DNSE_API]"


class OTPType(Enum):
    SMART = "smart"
    EMAIL = "email"


class AuthClient(BaseTradingClient):
    def __init__(
        self,
        account: Optional[str] = None,
        jwt_token: Optional[str] = None,
        trading_token: Optional[str] = None,
        config: Optional[TradingAPIConfig] = None,
    ):
        super().__init__(config)
        self.account = account
        self.jwt_token = jwt_token
        self.trading_token = trading_token
        self.storage = (
            RedisTokenStorage() if REDIS_AVAILABLE else SQLServerTokenStorage()
        )

    async def login(self, account: str, password: str) -> bool:
        try:
            url = f"{self.config.base_url}/auth-service/login"
            data = {"username": account, "password": password}
            response_data = await self.make_request(
                method="POST", url=url, include_jwt_token=False, json_data=data
            )

            jwt_token = response_data.get("token")
            self.account = account
            self.jwt_token = jwt_token

            current_time = TimeUtils.get_current_vn_time().strftime(
                SQLServerConsts.TRADING_TIME_FORMAT
            )

            existing_token = None
            try:
                existing_token = await self.storage.load_token(
                    account=account, broker="DNSE"
                )
            except:
                pass

            token_entity = TradingTokens(
                account=account,
                jwtToken=jwt_token,
                tradingToken=(
                    existing_token.tradingToken
                    if existing_token and existing_token.is_trading_token_valid()
                    else None
                ),
                broker="DNSE",
                jwtCreatedAt=current_time,
                tradingCreatedAt=(
                    existing_token.tradingCreatedAt
                    if existing_token and existing_token.is_trading_token_valid()
                    else None
                ),
            )

            await self.storage.save_token(token_data=token_entity)

            LOGGER.info(
                f"{LOGGER_PREFIX} Authentication successful for account: {account}"
            )
            return True

        except Exception as e:
            raise BaseExceptionResponse(
                http_code=401,
                status_code=401,
                message=MessageConsts.TRADING_API_ERROR,
                errors=str(e),
            )

    async def send_email_otp(self) -> bool:
        if not self.jwt_token or not self.account:
            LOGGER.error("No valid token available for OTP request")
            return False
        try:
            url = f"{self.config.base_url}/auth-service/api/email-otp"
            response_text = await self.make_request(
                "GET", url, include_jwt_token=True, expect_json=False
            )

            if isinstance(response_text, str) and "OK" in response_text.upper():
                LOGGER.info(f"{LOGGER_PREFIX} Email OTP sent successfully!")
                return True
            else:
                LOGGER.warning(
                    f"{LOGGER_PREFIX} Unexpected response from OTP endpoint: {response_text}"
                )
                return False

        except Exception as e:
            LOGGER.error(f"{LOGGER_PREFIX} Failed to send email OTP: {e}")
            raise BaseExceptionResponse(
                http_code=502,
                status_code=502,
                message=MessageConsts.TRADING_API_ERROR,
                errors=str(e),
            )

    async def get_trading_token(
        self, otp: str, otp_type: OTPType = OTPType.EMAIL.value
    ) -> bool:
        if not self.jwt_token:
            LOGGER.error("No valid token available for trading token request")
            return False

        try:
            url = f"{self.config.base_url}/order-service/trading-token"
            data = {}
            LOGGER.info(f"{LOGGER_PREFIX} OTP Type: {otp_type}")
            if otp_type == OTPType.SMART.value:
                data["smart-otp"] = otp
            elif otp_type == OTPType.EMAIL.value:
                data["otp"] = otp
            LOGGER.info(f"{LOGGER_PREFIX} Data to send: {data}")

            response_data = await self.make_request(
                method="POST", url=url, json_data=data
            )

            trading_token = response_data.get("tradingToken")
            if not trading_token:
                raise BaseExceptionResponse(
                    http_code=401,
                    status_code=401,
                    message=MessageConsts.TRADING_API_ERROR,
                    errors="Authentication failed",
                )

            self.trading_token = trading_token

            current_time = TimeUtils.get_current_vn_time().strftime(
                SQLServerConsts.TRADING_TIME_FORMAT
            )

            existing_token = await self.storage.load_token(
                account=self.account, broker="DNSE"
            )

            token_entity = TradingTokens(
                account=self.account,
                jwtToken=self.jwt_token,
                tradingToken=trading_token,
                broker="DNSE",
                jwtCreatedAt=(
                    existing_token.jwtCreatedAt if existing_token else current_time
                ),
                tradingCreatedAt=current_time,
                createdAt=existing_token.createdAt if existing_token else current_time,
                updatedAt=current_time,
            )

            if self.account:
                await self.storage.save_token(token_data=token_entity)

            LOGGER.info(
                f"{LOGGER_PREFIX} Trading token obtained and saved successfully!"
            )
            return True

        except Exception as e:
            LOGGER.error(f"{LOGGER_PREFIX} Failed to get trading token: {e}")
            raise BaseExceptionResponse(
                http_code=502,
                status_code=502,
                message=MessageConsts.TRADING_API_ERROR,
                errors=str(e),
            )

    async def load_token(self, account: str, broker: str = "DNSE") -> bool:
        try:
            token_data = await self.storage.load_token(account=account, broker=broker)

            if not token_data:
                LOGGER.info(
                    f"{LOGGER_PREFIX} No token found for account {account} in broker {broker}"
                )
                return False

            if token_data.jwtToken and token_data.is_jwt_valid():
                self.account = account
                self.jwt_token = token_data.jwtToken

                if token_data.tradingToken and token_data.is_trading_token_valid():
                    self.trading_token = token_data.tradingToken

                    # jwt_remaining = token_data.jwt_time_remaining()
                    # trading_remaining = token_data.trading_time_remaining()

                    LOGGER.info(f"{LOGGER_PREFIX} Token {account} loaded successfully.")
                    # LOGGER.info(f"{LOGGER_PREFIX} JWT remaining: {jwt_remaining}")
                    # LOGGER.info(f"{LOGGER_PREFIX} Trading token remaining: {trading_remaining}")
                else:
                    LOGGER.info(
                        f"{LOGGER_PREFIX} JWT loaded, but trading token is expired or missing"
                    )
                    self.trading_token = None

                return True
            else:
                if token_data.jwtToken and not token_data.is_jwt_valid():
                    LOGGER.warning(
                        f"{LOGGER_PREFIX} JWT token for {account} is expired"
                    )
                else:
                    LOGGER.warning(
                        f"{LOGGER_PREFIX} No valid JWT token for {account} found"
                    )
                return False
        except BaseExceptionResponse:
            raise
        except Exception as e:
            LOGGER.error(f"{LOGGER_PREFIX} Failed to load token: {e}")
            return False
