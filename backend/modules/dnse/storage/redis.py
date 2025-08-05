from typing import Optional, Dict
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


class RedisTokenStorage(BaseTokenStorage):
    def _get_token_key(self, account: str, broker: str) -> str:
        """Generate Redis key for token storage"""
        return f"token:{account}:{broker}"

    def _get_pattern_key(self, account: str) -> str:
        """Generate Redis pattern key to find all tokens for an account"""
        return f"token:{account}:*"

    async def save_token(self, token_data: TradingTokens) -> None:
        if not REDIS_AVAILABLE:
            LOGGER.warning("Redis is not available, cannot save token")
            return

        try:
            token_key = self._get_token_key(token_data.account, token_data.broker)

            existing_data = conn.hgetall(token_key)
            token_data_dict = token_data.to_dict()
            current_time = TimeUtils.get_current_vn_time().strftime(
                SQLServerConsts.TRADING_TIME_FORMAT
            )

            if existing_data:
                token_data_dict["updatedAt"] = current_time
                if existing_data.get("createdAt"):
                    token_data_dict["createdAt"] = existing_data["createdAt"]
                else:
                    token_data_dict["createdAt"] = current_time

                LOGGER.info(f"Updating existing token for account {token_data.account}")
            else:
                token_data_dict["id"] = str(uuid4())
                token_data_dict["createdAt"] = current_time
                token_data_dict["updatedAt"] = current_time
                LOGGER.info(f"Creating new token for account {token_data.account}")

            # Filter out None values for Redis storage
            redis_data = {k: v for k, v in token_data_dict.items() if v is not None}
            
            conn.hset(token_key, mapping=redis_data)
            LOGGER.info(
                f"Token for account {token_data.account} saved to Redis successfully."
            )

        except Exception as e:
            LOGGER.error(f"Error saving token to Redis: {e}")
            raise BaseExceptionResponse(
                http_code=500,
                status_code=500,
                message="Failed to save token to Redis",
                errors=str(e),
            )

    async def load_token(
        self, account: str, broker: str = "DNSE"
    ) -> Optional[TradingTokens]:
        if not REDIS_AVAILABLE:
            LOGGER.warning("Redis is not available, cannot load token")
            return None

        try:
            token_key = self._get_token_key(account, broker)
            data = conn.hgetall(token_key)

            if not data:
                LOGGER.info(f"No token found for account {account} in broker {broker}")
                return None

            pattern_key = self._get_pattern_key(account)
            all_keys = conn.keys(pattern_key)
            broker_keys = [key for key in all_keys if key.endswith(f":{broker}")]

            if len(broker_keys) > 1:
                LOGGER.error(
                    f"Multiple tokens found for account {account} in broker {broker}"
                )
                raise BaseExceptionResponse(
                    http_code=400,
                    status_code=400,
                    message="Duplicate trading tokens found",
                    errors=f"Multiple tokens found for account {account} in broker {broker}",
                )

            token = TradingTokens.from_dict(data)
            LOGGER.info(f"Token loaded for account {account} from Redis successfully")
            return token

        except Exception as e:
            LOGGER.error(f"Error loading token from Redis: {e}")
            raise BaseExceptionResponse(
                http_code=500,
                status_code=500,
                message="Failed to load token from Redis",
                errors=str(e),
            )

    async def delete_token(self, account: str, broker: str = "DNSE") -> None:
        if not REDIS_AVAILABLE:
            LOGGER.warning("Redis is not available, cannot delete token")
            return

        try:
            token_key = self._get_token_key(account, broker)

            existing_data = conn.hgetall(token_key)
            if not existing_data:
                LOGGER.warning(
                    f"No token found for account {account} in broker {broker}."
                )
                return

            pattern_key = self._get_pattern_key(account)
            all_keys = conn.keys(pattern_key)
            broker_keys = [key for key in all_keys if key.endswith(f":{broker}")]

            if len(broker_keys) > 1:
                LOGGER.error(
                    f"Multiple tokens found for account {account} in broker {broker}"
                )
                raise BaseExceptionResponse(
                    http_code=400,
                    status_code=400,
                    message="Duplicate trading tokens found",
                    errors=f"Multiple tokens found for account {account} in broker {broker}",
                )

            result = conn.delete(token_key)
            if result > 0:
                LOGGER.info(
                    f"Token for account {account} deleted from Redis successfully."
                )
            else:
                LOGGER.warning(
                    f"Token for account {account} was not found during deletion."
                )

        except BaseExceptionResponse:
            raise
        except Exception as e:
            LOGGER.error(f"Error deleting token from Redis: {e}")
            raise BaseExceptionResponse(
                http_code=500,
                status_code=500,
                message="Failed to delete token from Redis",
                errors=str(e),
            )

    async def cleanup(self) -> None:
        if not REDIS_AVAILABLE:
            LOGGER.warning("Redis is not available, cannot cleanup")
            return
        try:
            conn.close()
            LOGGER.info(f"Closed connection to Redis.")
        except Exception as e:
            LOGGER.error(f"Error closing connection to Redis: {e}")
            raise BaseExceptionResponse(
                http_code=500,
                status_code=500,
                message="Failed to cleanup Redis connection",
                errors=str(e),
            )
