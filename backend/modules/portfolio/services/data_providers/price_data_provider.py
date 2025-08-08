import pandas as pd
import pickle
import warnings
import redis
from typing import Optional
from datetime import timedelta

from backend.common.consts import SQLServerConsts
from backend.redis.client import REDIS_CLIENT
from backend.db.sessions import mart_session_scope
from backend.utils.logger import LOGGER
from backend.utils.time_utils import TimeUtils


try:
    redis_conn = REDIS_CLIENT.get_conn()
    redis_binary_conn = redis.Redis(
        connection_pool=redis.ConnectionPool(
            host=redis_conn.connection_pool.connection_kwargs.get("host"),
            port=redis_conn.connection_pool.connection_kwargs.get("port"),
            db=redis_conn.connection_pool.connection_kwargs.get("db", 0),
            password=redis_conn.connection_pool.connection_kwargs.get("password"),
            decode_responses=False,  # Keep binary data as bytes
            socket_timeout=10.0,
            socket_connect_timeout=10.0,
        )
    )
    redis_binary_conn.ping()
    REDIS_AVAILABLE = True
except Exception as e:
    LOGGER.error(f"Failed to connect to Redis: {e}")
    LOGGER.info("Redis is not available, falling back to SQL Server")
    REDIS_AVAILABLE = False


class PriceDataProvider:
    CACHE_TTL = 12 * 3600  # 12 hours in seconds
    CACHE_PREFIX = "STOCK_PRICE_DF"

    @classmethod
    async def get_price_data_pivoted(
        cls, from_date: Optional[str] = None, days_back: int = 63
    ) -> pd.DataFrame:
        if from_date is None:
            current_date = TimeUtils.get_current_vn_time()
            days_back = max(days_back, 63)
            from_date = (current_date - timedelta(days=days_back)).strftime(
                SQLServerConsts.DATE_FORMAT
            )

        cache_key = cls.generate_cache_key(from_date)

        cached_data = await cls.get_from_cache(cache_key)
        if cached_data is not None:
            LOGGER.info(f"📦 Cache HIT for price data: {cache_key}")
            return cached_data

        LOGGER.info(f"💾 Cache MISS for price data: {cache_key} - fetching from DB")

        df_pivoted = await cls.fetch_from_database(from_date)
        await cls.save_to_cache(cache_key, df_pivoted)

        return df_pivoted

    @classmethod
    def generate_cache_key(cls, from_date: str) -> str:
        key_components = [cls.CACHE_PREFIX, from_date, "all_symbols"]

        current_date = TimeUtils.get_current_vn_time()
        today = current_date.strftime(SQLServerConsts.DATE_FORMAT)
        key_components.append(f"cached-{today}")

        return ":".join(key_components)

    @classmethod
    async def get_from_cache(cls, cache_key: str) -> Optional[pd.DataFrame]:
        """Retrieve DataFrame from Redis cache"""
        try:
            # Use binary connection to avoid decoding issues
            cached_bytes = redis_binary_conn.get(cache_key)

            if cached_bytes:
                try:
                    df = pickle.loads(cached_bytes)

                    if isinstance(df, pd.DataFrame) and not df.empty:
                        LOGGER.debug(
                            f"✅ Successfully retrieved cached DataFrame: shape {df.shape}"
                        )
                        return df
                    else:
                        LOGGER.warning(
                            f"⚠️ Invalid cached DataFrame for key: {cache_key}"
                        )
                        redis_binary_conn.delete(cache_key)

                except (
                    pickle.UnpicklingError,
                    UnicodeDecodeError,
                    ValueError,
                ) as decode_error:
                    LOGGER.warning(
                        f"⚠️ Corrupted cache data for key {cache_key}: {str(decode_error)}"
                    )
                    # Delete the corrupted cache entry
                    redis_binary_conn.delete(cache_key)
                    return None

            return None

        except Exception as e:
            LOGGER.error(f"❌ Error retrieving from cache {cache_key}: {str(e)}")
            # Try to clean up potentially corrupted cache entry
            try:
                redis_binary_conn.delete(cache_key)
                LOGGER.info(f"🧹 Cleaned up corrupted cache entry: {cache_key}")
            except:
                pass
            return None

    @classmethod
    async def save_to_cache(cls, cache_key: str, df: pd.DataFrame) -> bool:
        """Save DataFrame to Redis cache"""
        try:
            if df.empty:
                LOGGER.warning("⚠️ Attempted to cache empty DataFrame - skipping")
                return False

            df_bytes = pickle.dumps(df, protocol=4)

            size_mb = len(df_bytes) / (1024 * 1024)
            if size_mb > 100:  # 100MB limit
                LOGGER.warning(
                    f"⚠️ DataFrame too large to cache: {size_mb:.2f}MB - skipping"
                )
                return False

            success = redis_binary_conn.setex(cache_key, cls.CACHE_TTL, df_bytes)

            if success:
                LOGGER.info(
                    f"💾 Cached DataFrame: key={cache_key}, shape={df.shape}, size={size_mb:.2f}MB, ttl={cls.CACHE_TTL}s"
                )
                return True
            else:
                LOGGER.warning(f"⚠️ Failed to set cache entry: {cache_key}")
                return False

        except Exception as e:
            LOGGER.error(f"❌ Error saving to cache {cache_key}: {str(e)}")
            return False

    @classmethod
    async def clear_cache_pattern(cls, pattern: str = None) -> int:
        """Clear cache entries matching a pattern. If no pattern provided, clears all price data cache."""
        try:
            if pattern is None:
                pattern = f"{cls.CACHE_PREFIX}:*"

            # Get all keys matching the pattern
            keys = redis_binary_conn.keys(pattern)

            if keys:
                deleted_count = redis_binary_conn.delete(*keys)
                LOGGER.info(
                    f"🧹 Cleared {deleted_count} cache entries matching pattern: {pattern}"
                )
                return deleted_count
            else:
                LOGGER.info(f"🔍 No cache entries found matching pattern: {pattern}")
                return 0

        except Exception as e:
            LOGGER.error(f"❌ Error clearing cache pattern {pattern}: {str(e)}")
            return 0

    @classmethod
    async def fetch_from_database(cls, from_date: str) -> pd.DataFrame:
        try:
            with mart_session_scope() as mart_session:

                sql_query = f"""
                    SET TRANSACTION ISOLATION LEVEL READ UNCOMMITTED;

                    WITH UncommittedData AS (
                        SELECT 
                            [ticker] 
                            ,[date] 
                            ,[closePriceAdjusted]
                            ,ROW_NUMBER() OVER (PARTITION BY [ticker], [date] ORDER BY __updatedAt__ DESC) AS rn
                        FROM [priceVolume].[priceVolume]
                        WHERE [date] >= '{from_date}'
                    )

                    SELECT [ticker], [date], [closePriceAdjusted]
                    FROM UncommittedData
                    WHERE rn = 1
                    ORDER BY [date], [ticker];
                """

                LOGGER.debug(f"🔍 Executing price data query: from_date={from_date}")

                with warnings.catch_warnings():
                    warnings.simplefilter("ignore", UserWarning)
                    conn = mart_session.connection().connection

                    # Fetch data
                    df_stock = pd.read_sql_query(sql_query, conn)

                    if df_stock.empty:
                        LOGGER.warning(
                            f"⚠️ No price data found for criteria: from_date={from_date}"
                        )
                        return pd.DataFrame()

                    # Pivot the data
                    df_stock_pivoted = df_stock.pivot(
                        index="date", columns="ticker", values="closePriceAdjusted"
                    )

                    LOGGER.info(
                        f"✅ Fetched price data from DB: shape={df_stock_pivoted.shape}, date_range={from_date} to {df_stock_pivoted.index.max()}"
                    )

                    return df_stock_pivoted

        except Exception as e:
            LOGGER.error(f"❌ Error fetching price data from database: {str(e)}")
            raise
