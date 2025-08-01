from contextlib import asynccontextmanager
from typing import Optional, AsyncGenerator
from backend.common.configs.dnse import TradingAPIConfig
from backend.modules.dnse.trading_api import AuthClient, OrdersClient, UsersClient


class DNSESession:
    def __init__(self, config: Optional[TradingAPIConfig] = None):
        self.config = config or TradingAPIConfig()
        self.auth_client: Optional[AuthClient] = None
        self._jwt_token: Optional[str] = None
        self._trading_token: Optional[str] = None

    async def __aenter__(self):
        self.auth_client = AuthClient(config=self.config)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.auth_client:
            await self.auth_client.cleanup()

    @property
    def jwt_token(self) -> Optional[str]:
        return self.auth_client.jwt_token if self.auth_client else self._jwt_token

    @property
    def trading_token(self) -> Optional[str]:
        return (
            self.auth_client.trading_token if self.auth_client else self._trading_token
        )

    async def authenticate(self, account: str, password: str) -> bool:
        if await self.auth_client.load_token(account=account):
            return True

        if await self.auth_client.login(account=account, password=password):
            return True
        return False

    async def send_otp(self) -> bool:
        return await self.auth_client.send_email_otp()

    async def complete_auth(self, otp: str, otp_type: str = "email") -> bool:
        return await self.auth_client.get_trading_token(otp=otp, otp_type=otp_type)

    def is_fully_authenticated(self) -> bool:
        return bool(self.jwt_token and self.trading_token)

    def is_jwt_authenticated(self) -> bool:
        return bool(self.jwt_token)

    def get_auth_status(self) -> dict:
        return {
            "has_jwt_token": bool(self.jwt_token),
            "has_trading_token": bool(self.trading_token),
            "fully_authenticated": self.is_fully_authenticated(),
            "can_trade": self.is_fully_authenticated(),
            "can_read_user_info": self.is_jwt_authenticated(),
        }

    @asynccontextmanager
    async def orders_client(self) -> AsyncGenerator[OrdersClient, None]:
        if not self.jwt_token:
            raise ValueError("JWT token is required for OrdersClient")
        if not self.trading_token:
            raise ValueError("Trading token is required for OrdersClient")

        client = OrdersClient(
            config=self.config,
            jwt_token=self.jwt_token,
            trading_token=self.trading_token,
        )
        try:
            yield client
        finally:
            await client.cleanup()

    @asynccontextmanager
    async def users_client(self) -> AsyncGenerator[UsersClient, None]:
        if not self.jwt_token:
            raise ValueError("JWT token is required for UsersClient")

        client = UsersClient(
            config=self.config,
            jwt_token=self.jwt_token,
            trading_token=self.trading_token,  
        )
        try:
            yield client
        finally:
            await client.cleanup()

