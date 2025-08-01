from typing import Optional, Dict

from backend.common.consts import MessageConsts
from backend.common.responses.exceptions.base_exceptions import BaseExceptionResponse
from backend.modules.base_trading_client import BaseTradingClient


class UsersClient(BaseTradingClient):
    async def get_users_info(self) -> Optional[Dict]:
        url = f"{self.config.base_url}/user-service/api/me"
        
        try:
            result = await self.make_request("GET", url)
            self.log_success("Get user's info successfully", result)
            return result
        except Exception as e:
            self.log_error("Failed to get user's info", e)
            raise BaseExceptionResponse(
                http_code=502,
                status_code=502,
                message=MessageConsts.TRADING_API_ERROR,
                errors=str(e)
            )
        
    async def get_user_accounts(self) -> Optional[Dict]:
        url = f"{self.config.base_url}/order-service/accounts"
        
        try:
            result = await self.make_request("GET", url)
            self.log_success("Get user's accounts successfully", result)
            return result
        except Exception as e:
            self.log_error("Failed to get user's accounts", e)
            raise BaseExceptionResponse(
                http_code=502,
                status_code=502,
                message=MessageConsts.TRADING_API_ERROR,
                errors=str(e)
            )

    async def get_buying_power(self, account_no: str, symbol: str, price: float, load_package_id: str) -> Optional[Dict]:
        url = f"{self.config.base_url}/order-service/accounts/{account_no}/ppse"
        params = {"symbol": symbol, "price": price, "loadPackageId": load_package_id}
        
        try:
            result = await self.make_request("GET", url, params=params)
            self.log_success("Get buying power successfully", result)
            return result
        except Exception as e:
            self.log_error("Failed to get buying power", e)
            raise BaseExceptionResponse(
                http_code=502,
                status_code=502,
                message=MessageConsts.TRADING_API_ERROR,
                errors=str(e)
            )