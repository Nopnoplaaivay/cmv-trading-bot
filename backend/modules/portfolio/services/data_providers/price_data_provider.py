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
    def __init__(self, prefix: str = "STOCK"):
        self.prefix = prefix
        self.cache_ttl = 12 * 3600

    async def get_market_data(self, from_date: Optional[str] = None) -> pd.DataFrame:
        if from_date is None:
            current_date = TimeUtils.get_current_vn_time()
            from_date = (current_date - timedelta(days=63)).strftime(
                SQLServerConsts.DATE_FORMAT
            )

        cache_key = self.generate_cache_key(from_date)

        cached_data = await self.get_from_cache(cache_key)
        if cached_data is not None:
            LOGGER.info(f"📦 Cache HIT for price data: {cache_key}")
            return cached_data

        LOGGER.info(f"💾 Cache MISS for price data: {cache_key} - fetching from DB")

        df_pivoted = await self.fetch_price_data_from_database(from_date)
        await self.save_to_cache(cache_key, df_pivoted)
        return df_pivoted

    def generate_cache_key(self, from_date: str) -> str:
        key_components = [self.prefix, from_date]

        current_date = TimeUtils.get_current_vn_time()
        today = current_date.strftime(SQLServerConsts.DATE_FORMAT)
        key_components.append(f"cached-{today}")

        return ":".join(key_components)

    @classmethod
    async def get_from_cache(self, cache_key: str) -> Optional[pd.DataFrame]:
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
                    redis_binary_conn.delete(cache_key)
                    return None

            return None

        except Exception as e:
            LOGGER.error(f"❌ Error retrieving from cache {cache_key}: {str(e)}")
            try:
                redis_binary_conn.delete(cache_key)
                LOGGER.info(f"🧹 Cleaned up corrupted cache entry: {cache_key}")
            except:
                pass
            return None

    async def save_to_cache(self, cache_key: str, df: pd.DataFrame) -> bool:
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

            success = redis_binary_conn.setex(cache_key, self.cache_ttl, df_bytes)

            if success:
                LOGGER.info(
                    f"💾 Cached DataFrame: key={cache_key}, shape={df.shape}, size={size_mb:.2f}MB, ttl={self.cache_ttl}s"
                )
                return True
            else:
                LOGGER.warning(f"⚠️ Failed to set cache entry: {cache_key}")
                return False

        except Exception as e:
            LOGGER.error(f"❌ Error saving to cache {cache_key}: {str(e)}")
            return False

    async def fetch_price_data_from_database(self, from_date: str) -> pd.DataFrame:
        try:
            with mart_session_scope() as mart_session:

                if self.prefix == "STOCK":
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
                elif self.prefix == "INDEX":
                    sql_query = f"""
                        SET TRANSACTION ISOLATION LEVEL READ UNCOMMITTED;

                        WITH UncommittedData AS (
                            SELECT 
                                [icbCode] 
                                ,[date] 
                                ,[closeIndex]
                                ,ROW_NUMBER() OVER (PARTITION BY [icbCode], [date] ORDER BY __updatedAt__ DESC) AS rn
                            FROM [priceVolume].[isPriceVolume]
                            WHERE [icbCode] = 'VNINDEX' AND [date] >= '{from_date}'
                        )

                        SELECT [icbCode], [date], [closeIndex]
                        FROM UncommittedData
                        WHERE rn = 1
                        ORDER BY [date], [icbCode];
                    """

                LOGGER.debug(f"🔍 Executing price data query: from_date={from_date}")

                with warnings.catch_warnings():
                    warnings.simplefilter("ignore", UserWarning)
                    conn = mart_session.connection().connection

                    # Fetch data
                    df = pd.read_sql_query(sql_query, conn)

                    if df.empty:
                        LOGGER.warning(
                            f"⚠️ No price data found for criteria: from_date={from_date}"
                        )
                        return pd.DataFrame()

                    # Pivot the data
                    if self.prefix == "STOCK":
                        df_pivoted = df.pivot(
                            index="date", columns="ticker", values="closePriceAdjusted"
                        )
                    elif self.prefix == "INDEX":
                        df_pivoted = df[["date", "closeIndex"]].copy()

                    LOGGER.info(
                        f"✅ Fetched price data from DB: shape={df_pivoted.shape}, date_range={from_date} to {df_pivoted.index.max()}"
                    )
                    return df_pivoted

        except Exception as e:
            LOGGER.error(f"❌ Error fetching price data from database: {str(e)}")
            raise e
