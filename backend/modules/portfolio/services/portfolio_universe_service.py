import time
import pandas as pd
import numpy as np
import warnings

warnings.filterwarnings(
    "ignore",
    message=".*Downcasting behavior in `replace` is deprecated.*",
    category=FutureWarning,
)
from scipy.stats import rankdata

from backend.common.consts import SQLServerConsts
from backend.modules.base_monthly import BaseMonthlyService
from backend.modules.portfolio.repositories import StocksUniverseRepo
from backend.db.sessions import mart_session_scope, lake_session_scope
from backend.utils.data_utils import DataUtils
from backend.utils.logger import LOGGER


LOGGER_PREFIX = "[StocksUniverseService]"
UNIVERSE_SIZE = 20


class StocksUniverseService(BaseMonthlyService):
    repo = StocksUniverseRepo

    @classmethod
    async def update_data(cls, from_date):
        start_time = time.time()
        with lake_session_scope() as lake_session:
            sql_query_0 = """
                SET TRANSACTION ISOLATION LEVEL READ UNCOMMITTED;

                WITH UncommittedData AS (
                    SELECT
                        [ticker]
                        ,[exchangeCode]
                    FROM [LakeEod].[appFiinxCommon].[stocks]
                )
                SELECT * FROM UncommittedData
                ORDER BY [ticker];
            """
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            conn = lake_session.connection().connection
            df_stock_0 = pd.read_sql_query(sql_query_0, conn)
        with mart_session_scope() as mart_session:
            sql_query_1 = f"""
                SET TRANSACTION ISOLATION LEVEL READ UNCOMMITTED;

                WITH UncommittedData AS (
                SELECT ticker, date, closePrice,  referencePriceAdjusted, openPriceAdjusted, highPriceAdjusted, lowPriceAdjusted, closePriceAdjusted, averagePriceAdjusted, beta2Y, beta6M, 
                totalMatchValue, totalMatchVolume, totalValue, totalVolume, adjustedRatioCumProd,
                ROW_NUMBER() OVER (PARTITION BY [ticker], [date] ORDER BY __updatedAt__ DESC) AS rn
                FROM [priceVolume].[priceVolume]
                )

                SELECT * FROM UncommittedData
                where rn = 1 and [date] >= '{from_date}'
                ORDER BY [date], ticker;
            """

            sql_query_2 = f"""
                SET TRANSACTION ISOLATION LEVEL READ UNCOMMITTED;

                WITH UncommittedData AS (
                SELECT ticker, date, 
                f0141 as cap,
                f0114 as roe,
                f0127 as eps,
                f0143 as pb,
                f0145 as pe,
                f0069 as grossProfitQoQ,
                f0073 as netIncomeQoQ,

                ROW_NUMBER() OVER (PARTITION BY [ticker], [date] ORDER BY __updatedAt__ DESC) AS rn

                FROM [fiin].[fiinFinancialRatio]
                )

                SELECT * FROM UncommittedData
                where rn = 1 and [date] >= '{from_date}'
                ORDER BY [date], ticker;
            """

            sql_query_3 = f"""
                SET TRANSACTION ISOLATION LEVEL READ UNCOMMITTED;

                WITH UncommittedData AS (
                SELECT ticker, sectorL2,
                ROW_NUMBER() OVER (PARTITION BY [ticker] ORDER BY [__updatedAt__] DESC) AS rn

                FROM [company].[organization]
                )

                SELECT * FROM UncommittedData
                where rn = 1
                ORDER BY ticker;
            """
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", UserWarning)
                conn = mart_session.connection().connection
                df_stock_1 = pd.read_sql_query(sql_query_1, conn)
                df_stock_2 = pd.read_sql_query(sql_query_2, conn)
                df_sector = pd.read_sql_query(sql_query_3, conn)

                df_stock_1 = df_stock_1.drop(columns=["rn"], errors="ignore")
                df_stock_2 = df_stock_2.drop(columns=["rn"], errors="ignore")
                df_sector = df_sector.drop(columns=["rn"], errors="ignore")

            df_stock_2["cap"] = df_stock_2.groupby(["ticker"], group_keys=False)[
                "cap"
            ].ffill()
            df_stock_2["roe"] = df_stock_2.groupby(["ticker"], group_keys=False)[
                "roe"
            ].ffill()
            df_stock_2["eps"] = df_stock_2.groupby(["ticker"], group_keys=False)[
                "eps"
            ].ffill()
            df_stock_2["pb"] = df_stock_2.groupby(["ticker"], group_keys=False)[
                "pb"
            ].ffill()
            df_stock_2["pe"] = df_stock_2.groupby(["ticker"], group_keys=False)[
                "pe"
            ].ffill()
            df_stock_2["grossProfitQoQ"] = df_stock_2.groupby(
                ["ticker"], group_keys=False
            )["grossProfitQoQ"].ffill()
            df_stock_2["netIncomeQoQ"] = df_stock_2.groupby(
                ["ticker"], group_keys=False
            )["netIncomeQoQ"].ffill()

        end_time = time.time()
        LOGGER.info(f"{LOGGER_PREFIX} DATA FETCH TIME: {end_time - start_time:.2f}s")

        df_stock = pd.merge(df_stock_1, df_stock_2, on=["date", "ticker"], how="left")
        df_stock = pd.merge(df_stock, df_stock_0, on=["ticker"], how="left")
        df_stock = pd.merge(df_stock, df_sector, on=["ticker"], how="left")

        df_stock["averageLiquidity21"] = df_stock.groupby("ticker")[
            "totalMatchVolume"
        ].transform(lambda x: x.rolling(21).mean())
        df_stock["averageLiquidity63"] = df_stock.groupby("ticker")[
            "totalMatchVolume"
        ].transform(lambda x: x.rolling(63).mean())
        df_stock["averageLiquidity252"] = df_stock.groupby("ticker")[
            "totalMatchVolume"
        ].transform(lambda x: x.rolling(252).mean())

        df_stock["date"] = pd.to_datetime(df_stock["date"])
        df_stock = df_stock.sort_values(["ticker", "date"])
        df_stock["year_month"] = df_stock["date"].dt.to_period("M")

        # Lấy ngày giao dịch cuối cùng trong tháng cho từng mã
        monthly_last_day = (
            df_stock.groupby(["ticker", "year_month"])["date"].max().reset_index()
        )
        monthly_last_day.columns = ["ticker", "year_month", "last_trading_date"]

        # Merge để chỉ giữ lại dữ liệu của ngày cuối tháng
        df_monthly = pd.merge(
            df_stock,
            monthly_last_day,
            left_on=["ticker", "date"],
            right_on=["ticker", "last_trading_date"],
            how="inner",
        )

        # Tạo thông tin tháng kế tiếp để dự báo
        df_monthly["next_month"] = df_monthly["date"].dt.to_period("M") + 1
        df_monthly["year"] = df_monthly["next_month"].dt.year
        df_monthly["month"] = df_monthly["next_month"].dt.month

        # Lọc và xử lý dữ liệu cần dùng
        df_filtered = df_monthly[
            [
                "date",
                "year",
                "month",
                "ticker",
                "exchangeCode",
                "sectorL2",
                "cap",
                "averageLiquidity21",
                "averageLiquidity63",
                "averageLiquidity252",
                "netIncomeQoQ",
                "grossProfitQoQ",
                "roe",
                "eps",
                "pe",
                "pb",
            ]
        ].copy()

        current_period = pd.Period.now(freq="M")
        df_filtered = df_filtered[
            pd.to_datetime(
                df_filtered["year"].astype(str) + "-" + df_filtered["month"].astype(str)
            ).dt.to_period("M")
            <= current_period
        ]
        df_filtered = df_filtered.rename(columns={"ticker": "symbol"})
        df_filtered = df_filtered.drop_duplicates()
        df_filtered = df_filtered.apply(
            lambda col: DataUtils.round_and_fix_near_zero_column(col)
        )

        # Fix for pandas FutureWarning: explicitly handle inf values replacement
        df_filtered = df_filtered.replace(
            {np.inf: np.nan, -np.inf: np.nan}
        ).infer_objects(copy=False)

        df_filtered = df_filtered.sort_values(
            by=["year", "month", "symbol"]
        ).reset_index(drop=True)
        df_filtered["date"] = df_filtered["date"].dt.strftime(
            SQLServerConsts.DATE_FORMAT
        )

        """
        FILTER 1: Lọc cơ bản về thanh khoản, vốn hóa, ngành và sàn giao dịch.
        """

        df_filtered = df_filtered.dropna(subset=["cap", "grossProfitQoQ"])

        min_market_cap = 1e12
        df_filtered = df_filtered[df_filtered["cap"] >= min_market_cap]

        min_avg_liquidity_63 = 1e4
        df_filtered = df_filtered[
            df_filtered["averageLiquidity63"] >= min_avg_liquidity_63
        ]

        exchanges = ["HOSE", "HNX"]
        df_filtered = df_filtered[df_filtered["exchangeCode"].isin(exchanges)]

        available_sectors = [
            "Financial Services",
            "Construction & Materials",
            "Real Estate",
            "Banks",
            "Basic Resources",
            "Retail",
        ]
        df_filtered = df_filtered[df_filtered["sectorL2"].isin(available_sectors)]

        """
        GROUP RANKING: Xếp hạng các cổ phiếu theo ROE và thanh khoản trung bình 21 ngày.
        """
        start_time = time.time()
        df_filtered["roe_group_rank"] = cls.apply_rank_by_date(
            df_filtered, "roe", "date", "sectorL2"
        )
        df_filtered["averageLiquidity21_group_rank"] = cls.apply_rank_by_date(
            df_filtered, "averageLiquidity21", "date", "sectorL2"
        )
        df_filtered["cap_group_rank"] = cls.apply_rank_by_date(
            df_filtered, "cap", "date", "sectorL2"
        )

        end_time = time.time()
        LOGGER.info(f"{LOGGER_PREFIX} GROUP RANKING TIME: {end_time - start_time:.2f}s")

        """
        FILTER 2: Lọc theo tiêu chí Chất lượng.
        """

        # Loại bỏ các mã thiếu dữ liệu cho lớp lọc này
        df_filtered = df_filtered.dropna(subset=["roe", "pe"])

        # Lọc theo ROE và D/E
        min_roe = 0.01
        min_gross_profit_qoq = 0.01
        df_filtered = df_filtered[
            (df_filtered["roe"] >= min_roe)
            & (df_filtered["grossProfitQoQ"] >= min_gross_profit_qoq)
        ]

        """
        FILTER 3: Xếp hạng các cổ phiếu còn lại và chọn ra 20 mã tốt nhất.
        """
        df_ranked = df_filtered.copy()
        df_ranked["CompositeScore"] = (
            df_ranked["roe_group_rank"] + df_ranked["averageLiquidity21_group_rank"]
        )

        final_df = pd.DataFrame()
        for year_month, group in df_ranked.groupby(["year", "month"]):
            top_stocks = group.nlargest(UNIVERSE_SIZE, "CompositeScore", keep="first")
            final_df = pd.concat([final_df, top_stocks], ignore_index=True)

        universe_df = final_df[
            [
                "date",
                "year",
                "month",
                "symbol",
                "exchangeCode",
                "sectorL2",
                "cap",
                "averageLiquidity21",
                "averageLiquidity63",
                "averageLiquidity252",
                "grossProfitQoQ",
                "roe",
                "eps",
                "pe",
                "pb",
            ]
        ]

        LOGGER.info(f"{LOGGER_PREFIX} DONE UPDATING UNIVERSE TOP {UNIVERSE_SIZE}\n")
        return universe_df

    @staticmethod
    def rank(x, rate=2):
        x = np.array(x)

        valid_mask = ~np.isnan(x)
        if not np.any(valid_mask):
            return np.full_like(x, np.nan, dtype=float)

        if rate == 0:
            ranks = rankdata(x[valid_mask], method="average")
        else:
            ranks = rankdata(x[valid_mask], method="average")

        n = np.sum(valid_mask)
        if n == 1:
            normalized_ranks = np.array([0.5])
        else:
            normalized_ranks = (ranks - 1) / (n - 1)

        result = np.full_like(x, np.nan, dtype=float)
        result[valid_mask] = normalized_ranks
        return result

    @classmethod
    def group_rank(cls, x, group):
        x = np.array(x)
        group = np.array(group)

        result = np.full_like(x, np.nan, dtype=float)
        valid_mask = ~np.isnan(x)
        valid_groups = group[valid_mask]
        unique_groups = np.unique(valid_groups[~pd.isna(valid_groups)])

        for g in unique_groups:
            group_mask = (group == g) & valid_mask
            if not np.any(group_mask):
                continue

            group_values = x[group_mask]
            group_ranks = cls.rank(group_values, rate=2)
            result[group_mask] = group_ranks

        return result

    @classmethod
    def apply_rank_by_date(cls, df, value_col, date_col="date", group_col=None):
        result = pd.Series(index=df.index, dtype=float)

        for date, group_data in df.groupby(date_col):
            values = group_data[value_col].values

            if group_col is not None:
                groups = group_data[group_col].values
                ranks = cls.group_rank(values, groups)
            else:
                ranks = cls.rank(values)

            result.loc[group_data.index] = ranks

        return result
