import asyncio
import aiohttp
import json
from typing import Optional, Dict, Any, Union
from dataclasses import dataclass
from enum import Enum
import time
from contextlib import asynccontextmanager

from src.utils.logger import LOGGER


class OrderSide(Enum):
    BUY = "BUY"
    SELL = "SELL"


class OrderType(Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"


@dataclass
class TradingConfig:
    """Configuration for trading operations"""
    base_url: str = "https://services.entrade.com.vn"
    timeout: int = 30
    max_retries: int = 3
    retry_delay: float = 1.0
    concurrent_limit: int = 10


class TradingAPIError(Exception):
    """Custom exception for trading API errors"""
    def __init__(self, message: str, status_code: Optional[int] = None, response_data: Optional[Dict] = None):
        self.message = message
        self.status_code = status_code
        self.response_data = response_data
        super().__init__(self.message)


class BaseTradingClient:
    """Base class with common functionality for trading operations"""
    
    def __init__(self, token: str, trading_token: str, config: Optional[TradingConfig] = None):
        self.token = token
        self.trading_token = trading_token
        self.config = config or TradingConfig()
        self.session: Optional[aiohttp.ClientSession] = None
        self.semaphore = asyncio.Semaphore(self.config.concurrent_limit)

    @asynccontextmanager
    async def get_session(self):
        """Context manager for HTTP session"""
        if self.session is None or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=self.config.timeout)
            self.session = aiohttp.ClientSession(timeout=timeout)
        
        try:
            yield self.session
        finally:
            # Session will be closed in cleanup method
            pass

    async def cleanup(self):
        """Clean up resources"""
        if self.session and not self.session.closed:
            await self.session.close()

    def get_headers(self, include_trading_token: bool = False) -> Dict[str, str]:
        """Generate headers for API requests"""
        headers = {"Authorization": f"Bearer {self.token}"}
        if include_trading_token:
            headers["Trading-Token"] = self.trading_token
        return headers

    async def request(
        self,
        method: str,
        url: str,
        params: Optional[Dict] = None,
        json_data: Optional[Dict] = None,
        include_trading_token: bool = False,
        retries: Optional[int] = None
    ) -> Dict[str, Any]:
        """Make HTTP request with retry logic and error handling"""
        
        if retries is None:
            retries = self.config.max_retries

        headers = self.get_headers(include_trading_token)
        
        async with self.semaphore:  # Limit concurrent requests
            for attempt in range(retries + 1):
                try:
                    async with self.get_session() as session:
                        async with session.request(
                            method=method,
                            url=url,
                            headers=headers,
                            params=params,
                            json=json_data
                        ) as response:
                            
                            response_data = await response.json()
                            
                            if response.status == 200:
                                return response_data
                            else:
                                error_msg = f"API request failed with status {response.status}"
                                if attempt == retries:
                                    raise TradingAPIError(error_msg, response.status, response_data)
                                
                                LOGGER.warning(f"{error_msg}. Attempt {attempt + 1}/{retries + 1}. Retrying...")
                                
                except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                    error_msg = f"Network error: {str(e)}"
                    if attempt == retries:
                        raise TradingAPIError(error_msg)
                    
                    LOGGER.warning(f"{error_msg}. Attempt {attempt + 1}/{retries + 1}. Retrying...")
                
                if attempt < retries:
                    await asyncio.sleep(self.config.retry_delay * (2 ** attempt))  # Exponential backoff

        raise TradingAPIError("Max retries exceeded")

    def log_success(self, operation: str, data: Dict[str, Any]):
        """Log successful operation"""
        LOGGER.info(f"{operation} thành công!")
        LOGGER.info(json.dumps(data, indent=4, ensure_ascii=False))

    def log_error(self, operation: str, error: Union[TradingAPIError, Exception]):
        """Log error operation"""
        if isinstance(error, TradingAPIError):
            LOGGER.error(f"{operation} thất bại: {error.message}")
            if error.response_data:
                LOGGER.error(json.dumps(error.response_data, indent=4, ensure_ascii=False))
        else:
            LOGGER.error(f"{operation} thất bại: {str(error)}")


class UnderlyingOrderManagement(BaseTradingClient):
    """Giao dịch cơ sở với async support và fault tolerance"""

    async def get_buying_power(self, account_no: str, symbol: str, price: float, load_package_id: str) -> Optional[Dict]:
        """1. Lấy thông tin sức mua GDCS"""
        url = f"{self.config.base_url}/dnse-order-service/accounts/{account_no}/ppse"
        params = {"symbol": symbol, "price": price, "loadPackageId": load_package_id}
        
        try:
            result = await self.make_request("GET", url, params=params)
            self.log_success("Lấy sức mua GDCS", result)
            return result
        except TradingAPIError as e:
            self.log_error("Lấy sức mua GDCS", e)
            return None

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
        """2. Đặt lệnh"""
        url = f"{self.config.base_url}/dnse-order-service/v2/orders"
        
        # Convert enums to strings if needed
        side_str = side.value if isinstance(side, OrderSide) else side
        order_type_str = order_type.value if isinstance(order_type, OrderType) else order_type
        
        data = {
            "symbol": symbol,
            "side": side_str,
            "orderType": order_type_str,
            "price": price,
            "quantity": quantity,
            "loanPackageId": loan_package_id,
            "accountNo": account_no,
        }
        
        try:
            result = await self.make_request("POST", url, json_data=data, include_trading_token=True)
            self.log_success(f"Đặt lệnh {side_str} {order_type_str} {quantity} {symbol}", result)
            return result
        except TradingAPIError as e:
            self.log_error("Đặt lệnh", e)
            return None

    async def get_order_book(self, account_no: str) -> Optional[Dict]:
        """3. Xem sổ lệnh"""
        url = f"{self.config.base_url}/dnse-order-service/v2/orders"
        params = {"accountNo": account_no}
        
        try:
            result = await self.make_request("GET", url, params=params)
            self.log_success("Lấy sổ lệnh GDCS", result)
            return result
        except TradingAPIError as e:
            self.log_error("Lấy sổ lệnh GDCS", e)
            return None

    async def get_order_detail(self, order_id: str, account_no: str) -> Optional[Dict]:
        """4. Chi tiết lệnh"""
        url = f"{self.config.base_url}/dnse-order-service/v2/orders/{order_id}"
        params = {"accountNo": account_no}
        
        try:
            result = await self.make_request("GET", url, params=params)
            self.log_success("Lấy chi tiết lệnh", result)
            return result
        except TradingAPIError as e:
            self.log_error("Lấy chi tiết lệnh", e)
            return None

    async def cancel_order(self, order_id: str, account_no: str) -> Optional[Dict]:
        """5. Hủy lệnh"""
        url = f"{self.config.base_url}/dnse-order-service/v2/orders/{order_id}"
        params = {"accountNo": account_no}
        
        try:
            result = await self.make_request("DELETE", url, params=params, include_trading_token=True)
            self.log_success("Hủy lệnh", result)
            return result
        except TradingAPIError as e:
            self.log_error("Hủy lệnh", e)
            return None

    async def get_deals(self, account_no: str) -> Optional[Dict]:
        """6. Danh sách deal nắm giữ"""
        url = f"{self.config.base_url}/dnse-deal-service/deals"
        params = {"accountNo": account_no}
        
        try:
            result = await self.make_request("GET", url, params=params)
            self.log_success("Lấy danh sách deal nắm giữ", result)
            return result
        except TradingAPIError as e:
            self.log_error("Lấy danh sách deal nắm giữ", e)
            return None

    async def batch_operations(self, operations: list) -> list:
        """Execute multiple operations concurrently"""
        tasks = []
        for op in operations:
            method_name = op.pop('method')
            method = getattr(self, method_name)
            tasks.append(method(**op))
        
        return await asyncio.gather(*tasks, return_exceptions=True)



# Usage example
async def main():
    """Example usage of the refactored trading clients"""
    config = TradingConfig(timeout=60, max_retries=5, concurrent_limit=20)
    
    # Initialize clients
    underlying_client = UnderlyingOrderManagement("your_token", "your_trading_token", config)
    
    try:
        # Single operations
        buying_power = await underlying_client.get_buying_power("account123", "VCB", 85000, "1036")
        
        # Batch operations
        operations = [
            {"method": "get_buying_power", "account_no": "account123", "symbol": "VCB", "price": 85000, "load_package_id": "1036"},
            {"method": "get_order_book", "account_no": "account123"},
            {"method": "get_deals", "account_no": "account123"}
        ]
        
        results = await underlying_client.batch_operations(operations)
        
        # Place order with enum
        order_result = await underlying_client.place_order(
            account_no="account123",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            symbol="VCB",
            price=85000,
            quantity=100
        )
        
    finally:
        # Clean up resources
        await underlying_client.cleanup()


if __name__ == "__main__":
    asyncio.run(main())