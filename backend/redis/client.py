import os
import redis

from backend.utils.logger import LOGGER


class RedisConnectionPool:
    def __init__(
        self,
        host,
        port=6379,
        password=None,
        db=0,
        decode_responses=True,
        socket_timeout=10.0,
        socket_connect_timeout=10.0,
    ):
        self.pool = redis.ConnectionPool(
            host=host,
            port=port,
            db=db,
            password=password,
            decode_responses=decode_responses,
            socket_timeout=socket_timeout,
            socket_connect_timeout=socket_connect_timeout,
        )

    def get_conn(self):
        """Lấy một kết nối Redis từ pool."""
        try:
            conn = redis.Redis(connection_pool=self.pool)
            conn.ping()
            return conn
        except redis.ConnectionError as e:
            LOGGER.error(f"Failed to connect to Redis server: {e}")
            return None


host = os.getenv("REDIS_HOST", "localhost")
port = int(os.getenv("REDIS_PORT", 6379))
password = os.getenv("REDIS_PASS", None)

REDIS_CLIENT = RedisConnectionPool(
    host=host,
    port=port,
    password=password,
    socket_timeout=10.0,
    socket_connect_timeout=10.0,
)
