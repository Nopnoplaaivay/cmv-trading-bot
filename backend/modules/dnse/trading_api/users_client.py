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

   