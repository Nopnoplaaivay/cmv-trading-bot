import json
from typing import Optional, Any
from cachetools import TTLCache
from backend.redis.client import REDIS_CLIENT
from backend.utils.logger import LOGGER


class RedisBlacklist:
    def __init__(self, maxsize: int = 1000, ttl: int = 24 * 60 * 60):
        self.redis_client = None
        self.fallback_cache = TTLCache(maxsize=maxsize, ttl=ttl)
        self.ttl = ttl
        self._initialize_redis()

    def _initialize_redis(self) -> None:
        """Initialize Redis connection with error handling."""
        try:
            self.redis_client = REDIS_CLIENT.get_conn()
            if self.redis_client:
                LOGGER.info("RedisBlacklist: Successfully connected to Redis")
            else:
                LOGGER.warning(
                    "RedisBlacklist: Failed to connect to Redis, using TTLCache fallback"
                )
        except Exception as e:
            LOGGER.error(f"RedisBlacklist: Redis initialization error: {e}")
            self.redis_client = None

    def _is_redis_available(self) -> bool:
        """Check if Redis connection is available."""
        if not self.redis_client:
            return False

        try:
            self.redis_client.ping()
            return True
        except Exception as e:
            LOGGER.warning(
                f"RedisBlacklist: Redis ping failed: {e}, switching to fallback"
            )
            self.redis_client = None
            return False

    def __setitem__(self, key: str, value: Any) -> None:
        """Set an item in the blacklist with TTL."""
        if self._is_redis_available():
            try:
                # Store in Redis with TTL
                serialized_value = json.dumps(value) if value is not None else ""
                self.redis_client.setex(f"blacklist:{key}", self.ttl, serialized_value)
                LOGGER.debug(f"RedisBlacklist: Set key {key} in Redis")
                return
            except Exception as e:
                LOGGER.error(f"RedisBlacklist: Failed to set key {key} in Redis: {e}")
                # Reinitialize Redis client
                self._initialize_redis()

        # Fallback to TTLCache
        self.fallback_cache[key] = value
        LOGGER.debug(f"RedisBlacklist: Set key {key} in TTLCache fallback")

    def __getitem__(self, key: str) -> Any:
        """Get an item from the blacklist."""
        if self._is_redis_available():
            try:
                value = self.redis_client.get(f"blacklist:{key}")
                if value is not None:
                    # Deserialize the value
                    return json.loads(value) if value else None
                # Key not found in Redis, raise KeyError
                raise KeyError(key)
            except KeyError:
                raise
            except Exception as e:
                LOGGER.error(f"RedisBlacklist: Failed to get key {key} from Redis: {e}")
                # Reinitialize Redis client
                self._initialize_redis()

        # Fallback to TTLCache
        return self.fallback_cache[key]

    def __contains__(self, key: str) -> bool:
        """Check if a key exists in the blacklist."""
        if self._is_redis_available():
            try:
                exists = self.redis_client.exists(f"blacklist:{key}")
                return bool(exists)
            except Exception as e:
                LOGGER.error(f"RedisBlacklist: Failed to check key {key} in Redis: {e}")
                self._initialize_redis()

        return key in self.fallback_cache

    def __delitem__(self, key: str) -> None:
        if self._is_redis_available():
            try:
                self.redis_client.delete(f"blacklist:{key}")
                LOGGER.debug(f"RedisBlacklist: Deleted key {key} from Redis")
                return
            except Exception as e:
                LOGGER.error(
                    f"RedisBlacklist: Failed to delete key {key} from Redis: {e}"
                )
                # Reinitialize Redis client
                self._initialize_redis()

        # Fallback to TTLCache
        if key in self.fallback_cache:
            del self.fallback_cache[key]
            LOGGER.debug(f"RedisBlacklist: Deleted key {key} from TTLCache fallback")

    def get(self, key: str, default: Any = None) -> Any:
        try:
            return self[key]
        except KeyError:
            return default

    def clear(self) -> None:
        """Clear all items from the blacklist."""
        if self._is_redis_available():
            try:
                # Delete all blacklist keys
                pattern = "blacklist:*"
                keys = self.redis_client.keys(pattern)
                if keys:
                    self.redis_client.delete(*keys)
                LOGGER.info("RedisBlacklist: Cleared all Redis blacklist keys")
                return
            except Exception as e:
                LOGGER.error(f"RedisBlacklist: Failed to clear Redis blacklist: {e}")
                # Reinitialize Redis client
                self._initialize_redis()

        # Fallback to TTLCache
        self.fallback_cache.clear()
        LOGGER.info("RedisBlacklist: Cleared TTLCache fallback")

    def keys(self):
        """Get all keys from the blacklist."""
        if self._is_redis_available():
            try:
                redis_keys = self.redis_client.keys("blacklist:*")
                # Remove the "blacklist:" prefix
                return [key.replace("blacklist:", "", 1) for key in redis_keys]
            except Exception as e:
                LOGGER.error(f"RedisBlacklist: Failed to get keys from Redis: {e}")
                # Reinitialize Redis client
                self._initialize_redis()

        # Fallback to TTLCache
        return list(self.fallback_cache.keys())

    def __len__(self) -> int:
        """Get the number of items in the blacklist."""
        if self._is_redis_available():
            try:
                return len(self.redis_client.keys("blacklist:*"))
            except Exception as e:
                LOGGER.error(f"RedisBlacklist: Failed to get length from Redis: {e}")
                # Reinitialize Redis client
                self._initialize_redis()

        # Fallback to TTLCache
        return len(self.fallback_cache)

    def __str__(self) -> str:
        """String representation of the blacklist."""
        storage_type = "Redis" if self._is_redis_available() else "TTLCache"
        return f"RedisBlacklist(storage={storage_type}, size={len(self)})"

    def get_storage_info(self) -> dict:
        """Get information about the current storage backend."""
        return {
            "is_redis_available": self._is_redis_available(),
            "storage_type": "Redis" if self._is_redis_available() else "TTLCache",
            "size": len(self),
            "ttl": self.ttl,
        }
