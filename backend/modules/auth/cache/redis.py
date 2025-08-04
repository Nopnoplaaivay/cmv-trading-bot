from typing import Optional, Union
from uuid import uuid4

from backend.common.consts import SQLServerConsts
from backend.common.responses.exceptions import BaseExceptionResponse
from backend.modules.dnse.entities import TradingTokens
from backend.modules.dnse.storage.base import BaseTokenStorage
from backend.redis.client import REDIS_CLIENT
from backend.utils.logger import LOGGER
from backend.utils.time_utils import TimeUtils

try:
    conn = REDIS_CLIENT.get_conn()
    REDIS_AVAILABLE = True
except Exception as e:
    LOGGER.error(f"Failed to connect to Redis: {e}")
    LOGGER.info("Redis is not available, falling back to SQL Server")
    REDIS_AVAILABLE = False


class RedisBlacklist:
    @staticmethod
    def set_session(key: str, value: int) -> None:
        if REDIS_AVAILABLE:
            try:
                conn.hset(f"SESSION_BLACKLIST:{key}", mapping={"exp": value})
            except Exception as e:
                LOGGER.error(f"Failed to set Redis blacklist item: {e}")

    @staticmethod
    def get_session(key: str) -> Optional[str]:
        if REDIS_AVAILABLE:
            try:
                return conn.hget(f"SESSION_BLACKLIST:{key}", "exp")
            except Exception as e:
                LOGGER.error(f"Failed to get Redis blacklist item: {e}")
        return None
        