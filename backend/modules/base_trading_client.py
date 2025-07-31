import asyncio
import aiohttp
import json
from typing import Optional, Dict, Any, Union

from enum import Enum
from contextlib import asynccontextmanager

from backend.common.consts import MessageConsts
from backend.common.configs.dnse import TradingAPIConfig
from backend.common.responses.exceptions.base_exceptions import BaseExceptionResponse
from backend.utils.logger import LOGGER


class OrderSide(Enum):
    BUY = "BUY"
    SELL = "SELL"


class OrderType(Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"


class BaseTradingClient:
    def __init__(
        self,
        config: Optional[TradingAPIConfig] = None,
        jwt_token: Optional[str] = None,
        trading_token: Optional[str] = None,
    ):
        self.jwt_token = jwt_token
        self.trading_token = trading_token
        self.config = config or TradingAPIConfig()
        self.session: Optional[aiohttp.ClientSession] = None
        self.semaphore = asyncio.Semaphore(self.config.concurrent_limit)

    @asynccontextmanager
    async def get_session(self):
        if self.session is None or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=self.config.timeout)
            self.session = aiohttp.ClientSession(timeout=timeout)
        try:
            yield self.session
        finally:
            pass

    async def cleanup(self):
        if self.session and not self.session.closed:
            await self.session.close()

    def get_headers(
        self, include_jwt_token: bool = True, include_trading_token: bool = False
    ) -> Dict[str, str]:
        if not include_jwt_token:
            return {}
        headers = {"Authorization": f"Bearer {self.jwt_token}"}
        if include_trading_token:
            headers["Trading-Token"] = self.trading_token
        return headers

    async def make_request(
        self,
        method: str,
        url: str,
        params: Optional[Dict] = None,
        json_data: Optional[Dict] = None,
        include_jwt_token: bool = True,
        include_trading_token: bool = False,
        retries: Optional[int] = None,
        expect_json: bool = True,
    ) -> Union[Dict[str, Any], str]:
        if retries is None:
            retries = self.config.max_retries

        headers = self.get_headers(
            include_jwt_token=include_jwt_token,
            include_trading_token=include_trading_token,
        )

        async with self.semaphore:
            for attempt in range(retries + 1):
                try:
                    async with self.get_session() as session:
                        async with session.request(
                            method=method,
                            url=url,
                            headers=headers,
                            params=params,
                            json=json_data,
                        ) as response:

                            if response.status == 200:
                                if expect_json:
                                    response_data = await response.json()
                                    return response_data
                                else:
                                    response_text = await response.text()
                                    return response_text
                            else:
                                # Read response data for error cases
                                try:
                                    if expect_json:
                                        error_response_data = await response.json()
                                    else:
                                        error_response_data = await response.text()
                                except:
                                    error_response_data = f"Could not parse response body (status: {response.status})"

                                error_msg = (
                                    f"API request failed with status {response.status}"
                                )
                                if attempt == retries:
                                    raise BaseExceptionResponse(
                                        http_code=response.status,
                                        status_code=MessageConsts.TRADING_API_ERROR,
                                        message=error_msg,
                                        errors=error_response_data,
                                    )
                                LOGGER.warning(
                                    f"{error_msg}. Attempt {attempt + 1}/{retries + 1}. Retrying..."
                                )

                except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                    error_msg = f"Network error: {str(e)}"
                    if attempt == retries:
                        raise BaseExceptionResponse(
                            http_code=500,
                            status_code=MessageConsts.TRADING_API_ERROR,
                            message=error_msg,
                            errors=str(e),
                        )

                    LOGGER.warning(
                        f"{error_msg}. Attempt {attempt + 1}/{retries + 1}. Retrying..."
                    )

                if attempt < retries:
                    await asyncio.sleep(
                        self.config.retry_delay * (2**attempt)
                    )  # Exponential backoff

        raise BaseExceptionResponse(
            http_code=500,
            status_code=MessageConsts.TRADING_API_ERROR,
            message="Max retries exceeded",
            errors="Failed to complete the request after multiple attempts",
        )

    def log_success(self, operation: str, data: Dict[str, Any]):
        LOGGER.info(f"{operation} successfully!")
        LOGGER.info(json.dumps(data, indent=4, ensure_ascii=False))

    def log_error(self, operation: str, error: Union[BaseExceptionResponse, Exception]):
        if isinstance(error, BaseExceptionResponse):
            LOGGER.error(f"{operation} failed: {error.message}")
            if error.response_data:
                LOGGER.error(
                    json.dumps(error.response_data, indent=4, ensure_ascii=False)
                )
        else:
            LOGGER.error(f"{operation} failed: {str(error)}")
