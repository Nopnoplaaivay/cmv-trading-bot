import asyncio
import aiohttp
import json
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Union, Protocol
from dataclasses import dataclass, asdict
from abc import ABC, abstractmethod
from enum import Enum
import os
from contextlib import asynccontextmanager
from typing import Optional, Dict, Union
from enum import Enum


from backend.common.consts import MessageConsts
from backend.common.configs.dnse import AuthConfig
from backend.common.responses.exceptions.base_exceptions import BaseExceptionResponse
from backend.modules.dnse.entities import TradingTokens
from backend.modules.base_trading_client import BaseTradingClient
from backend.modules.dnse.storage import RedisTokenStorage, SQLServerTokenStorage, REDIS_AVAILABLE
from backend.utils.logger import LOGGER




class OTPType(Enum):
    SMART = "smart"
    EMAIL = "email"


class TokensClient(BaseTradingClient):
    def __init__(
        self,
        account: Optional[str] = None,
        jwt_token: Optional[str] = None,
        trading_token: Optional[str] = None,
        config: Optional[AuthConfig] = None,
    ):
        super().__init__(config)
        self.account = account
        self.jwt_token = jwt_token
        self.trading_token = trading_token
        # self.current_token_data: Optional[TradingTokens] = None
        self.storage = (
            RedisTokenStorage() if REDIS_AVAILABLE else SQLServerTokenStorage()
        )

    async def get_jwt_token(self, account: str, password: str) -> bool:
        try:
            url = f"{self.config.base_url}/auth-service/login"
            data = {"username": account, "password": password}
            response_data = await self.make_request(
                method="POST", url=url, include_jwt_token=False, json_data=data
            )

            jwt_token = response_data.get("token")
            self.account = account
            self.jwt_token = jwt_token

            LOGGER.info(f"Authentication successful for account: {account}")
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
                LOGGER.info("Email OTP sent successfully!")
                return True
            else:
                LOGGER.warning(
                    f"Unexpected response from OTP endpoint: {response_text}"
                )
                return False

        except Exception as e:
            LOGGER.error(f"Failed to send email OTP: {e}")
            raise BaseExceptionResponse(
                http_code=502,
                status_code=502,
                message=MessageConsts.TRADING_API_ERROR,
                errors=str(e),
            )

    async def get_new_trading_token(
        self, otp: str, otp_type: OTPType = OTPType.EMAIL.value
    ) -> bool:
        if not self.jwt_token:
            LOGGER.error("No valid token available for trading token request")
            return False

        try:
            url = f"{self.config.base_url}/order-service/trading-token"
            data = {}
            print(f"OTP Type: {otp_type}")
            if otp_type == OTPType.SMART.value:
                data["smart-otp"] = otp
            elif otp_type == OTPType.EMAIL.value:
                data["otp"] = otp
            print(f"Data to send: {data}")

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
            token_entity = TradingTokens(
                account=self.account,
                jwtToken=self.jwt_token,
                tradingToken=trading_token,
                broker="DNSE",
            )

            if self.account:
                await self.storage.save_token(token_data=token_entity)

            LOGGER.info("Trading token obtained and saved successfully!")
            return True

        except Exception as e:
            LOGGER.error(f"Failed to get trading token: {e}")
            raise BaseExceptionResponse(
                http_code=502,
                status_code=502,
                message=MessageConsts.TRADING_API_ERROR,
                errors=str(e),
            )

    async def load_token(self, account: str, broker: str = "DNSE") -> bool:
        try:
            token_data = await self.storage.load_token(account=account, broker=broker)

            # Check if token_data is None first
            if not token_data:
                LOGGER.info(f"No token found for account {account} in broker {broker}")
                return False

            if (
                token_data.tradingToken
                and token_data.jwtToken
                and token_data.is_valid()
            ):
                self.jwt_token = token_data.jwtToken
                self.trading_token = token_data.tradingToken

                remaining = token_data.time_remaining()
                if remaining:
                    LOGGER.info(
                        f"Token loaded successfully. Time remaining: {remaining}"
                    )
                else:
                    LOGGER.info("Token loaded successfully (no expiry)")

                return True
            else:
                # refresh token if it's not valid
                LOGGER.warning(
                    "Token is not valid or missing tradingToken/jwtToken, attempting to refresh"
                )
                if not token_data.tradingToken or not token_data.jwtToken:
                    raise BaseExceptionResponse(
                        http_code=401,
                        status_code=401,
                        message=MessageConsts.TRADING_API_ERROR,
                        errors="Token data is incomplete",
                    )
                if not token_data.is_valid():
                    LOGGER.warning("Token is expired, refreshing...")
                    raise BaseExceptionResponse(
                        http_code=401,
                        status_code=401,
                        message=MessageConsts.TRADING_API_ERROR,
                        errors="Token is expired",
                    )

        except BaseExceptionResponse:
            raise
        except Exception as e:
            LOGGER.error(f"Failed to load token: {e}")
            return False
