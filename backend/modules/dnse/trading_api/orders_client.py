import asyncio
from typing import Optional, Dict, Union
from enum import Enum

from backend.common.consts import MessageConsts, DNSEConsts
from backend.common.responses.exceptions.base_exceptions import BaseExceptionResponse
from backend.modules.base_trading_client import BaseTradingClient


LOGGER_PREFIX = "[DNSE_API]"


class OrderSide(Enum):
    BUY = "NB"
    SELL = "NS"


class OrderType(Enum):
    MARKET = "MP"
    LIMIT = "LO"


class OrdersClient(BaseTradingClient):
    async def place_order(
        self,
        account_no: str,
        side: Union[OrderSide, str],
        order_type: Union[OrderType, str],
        symbol: str,
        price: float,
        quantity: int,
        loan_package_id: str = "1036"
    ) -> Optional[Dict]:
        url = f"{self.config.base_url}/order-service/v2/orders"

        data = {
            "symbol": symbol,
            "side": side,
            "orderType": order_type,
            "price": price,
            "quantity": quantity,
            "loanPackageId": loan_package_id,
            "accountNo": account_no,
        }
        
        try:
            result = await self.make_request("POST", url, json_data=data, include_trading_token=True)
            self.log_success(f"{LOGGER_PREFIX} Place order successfully: {side} {order_type} {quantity} {symbol}", result)
            return result
        except Exception as e:
            self.log_error(f"{LOGGER_PREFIX} Failed to place order: {side} {order_type} {quantity} {symbol}", e)
            raise BaseExceptionResponse(
                http_code=502,
                status_code=502,
                message=MessageConsts.TRADING_API_ERROR,
                errors=str(e)
            )
        
    async def get_order_book(self, account_no: str) -> Optional[Dict]:
        url = f"{self.config.base_url}/order-service/v2/orders"
        params = {"accountNo": account_no}
        
        try:
            result = await self.make_request("GET", url, params=params)
            self.log_success(f"{LOGGER_PREFIX} Get order book successfully", result)
            return result
        except Exception as e:
            self.log_error(f"{LOGGER_PREFIX} Failed to get order book", e)
            raise BaseExceptionResponse(
                http_code=502,
                status_code=502,
                message=MessageConsts.TRADING_API_ERROR,
                errors=str(e)
            )

    async def get_order_detail(self, order_id: str, account_no: str) -> Optional[Dict]:
        url = f"{self.config.base_url}/order-service/v2/orders/{order_id}"
        params = {"accountNo": account_no}
        
        try:
            result = await self.make_request("GET", url, params=params)
            self.log_success(f"{LOGGER_PREFIX} Get order detail successfully", result)
            return result
        except Exception as e:
            self.log_error("Failed to get order detail", e)
            raise BaseExceptionResponse(
                http_code=502,
                status_code=502,
                message=MessageConsts.TRADING_API_ERROR,
                errors=str(e)
            )

    async def cancel_order(self, order_id: str, account_no: str) -> Optional[Dict]:
        url = f"{self.config.base_url}/order-service/v2/orders/{order_id}"
        params = {"accountNo": account_no}
        
        try:
            result = await self.make_request("DELETE", url, params=params, include_trading_token=True)
            self.log_success(f"{LOGGER_PREFIX} Cancel order successfully", result)
            return result
        except Exception as e:
            self.log_error(f"{LOGGER_PREFIX} Failed to cancel order", e)
            raise BaseExceptionResponse(
                http_code=502,
                status_code=502,
                message=MessageConsts.TRADING_API_ERROR,
                errors=str(e)
            )

    async def get_deals(self, account_no: str) -> Optional[Dict]:
        url = f"{self.config.base_url}/deal-service/deals"
        params = {"accountNo": account_no}
        
        try:
            result = await self.make_request("GET", url, params=params)
            self.log_success(f"{LOGGER_PREFIX} Get held deals successfully", result)
            return result
        except Exception as e:
            self.log_error(f"{LOGGER_PREFIX} Failed to get held deals", e)
            raise BaseExceptionResponse(
                http_code=502,
                status_code=502,
                message=MessageConsts.TRADING_API_ERROR,
                errors=str(e)
            )

    async def batch_operations(self, operations: list) -> list:
        tasks = []
        for op in operations:
            method_name = op.pop('method')
            method = getattr(self, method_name)
            tasks.append(method(**op))
        
        return await asyncio.gather(*tasks, return_exceptions=True)