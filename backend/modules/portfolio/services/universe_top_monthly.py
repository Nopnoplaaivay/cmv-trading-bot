import pandas as pd
import numpy as np

from backend.common.consts import SQLServerConsts
from backend.modules.base_monthly import BaseMonthlyService
from backend.modules.portfolio.repositories import UniverseTopMonthlyRepo
from backend.db.sessions import mart_session_scope, lake_session_scope
from backend.utils.data_utils import DataUtils
from backend.utils.logger import LOGGER

class UniverseTopMonthlyService(BaseMonthlyService):
    repo = UniverseTopMonthlyRepo

    @classmethod
    async def update_data(cls, from_date):
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
            conn = mart_session.connection().connection
            df_stock_1 = pd.read_sql_query(sql_query_1, conn)
            df_stock_2 = pd.read_sql_query(sql_query_2, conn)
            df_sector = pd.read_sql_query(sql_query_3, conn)

            df_stock_1 = df_stock_1.drop(columns=['rn'], errors='ignore')
            df_stock_2 = df_stock_2.drop(columns=['rn'], errors='ignore')
            df_sector = df_sector.drop(columns=['rn'], errors='ignore')

            df_stock_2['cap'] = df_stock_2.groupby(["ticker"], group_keys=False)["cap"].ffill()
            df_stock_2['roe'] = df_stock_2.groupby(["ticker"], group_keys=False)["roe"].ffill()
            df_stock_2['eps'] = df_stock_2.groupby(["ticker"], group_keys=False)["eps"].ffill()
            df_stock_2['pb'] = df_stock_2.groupby(["ticker"], group_keys=False)["pb"].ffill()
            df_stock_2['pe'] = df_stock_2.groupby(["ticker"], group_keys=False)["pe"].ffill()
            df_stock_2['grossProfitQoQ'] = df_stock_2.groupby(["ticker"], group_keys=False)["grossProfitQoQ"].ffill()
            df_stock_2['netIncomeQoQ'] = df_stock_2.groupby(["ticker"], group_keys=False)["netIncomeQoQ"].ffill()

        df_stock = pd.merge(df_stock_1, df_stock_2, on=['date', 'ticker'], how="left")
        df_stock = pd.merge(df_stock, df_stock_0, on=['ticker'], how="left")
        df_stock = pd.merge(df_stock, df_sector, on=['ticker'], how="left")

        df_stock['averageLiquidity21'] = df_stock.groupby('ticker')['totalMatchVolume'].transform(lambda x: x.rolling(21).mean())
        df_stock['averageLiquidity63'] = df_stock.groupby('ticker')['totalMatchVolume'].transform(lambda x: x.rolling(63).mean())
        df_stock['averageLiquidity252'] = df_stock.groupby('ticker')['totalMatchVolume'].transform(lambda x: x.rolling(252).mean())

        df_stock['date'] = pd.to_datetime(df_stock['date'])
        df_stock = df_stock.sort_values(['ticker', 'date'])
        df_stock['year_month'] = df_stock['date'].dt.to_period('M')

        # Lấy ngày giao dịch cuối cùng trong tháng cho từng mã
        monthly_last_day = df_stock.groupby(['ticker', 'year_month'])['date'].max().reset_index()
        monthly_last_day.columns = ['ticker', 'year_month', 'last_trading_date']

        # Merge để chỉ giữ lại dữ liệu của ngày cuối tháng
        df_monthly = pd.merge(df_stock, monthly_last_day,
                              left_on=['ticker', 'date'],
                              right_on=['ticker', 'last_trading_date'],
                              how='inner')

        # Tạo thông tin tháng kế tiếp để dự báo
        df_monthly['next_month'] = df_monthly['date'].dt.to_period('M') + 1
        df_monthly['year'] = df_monthly['next_month'].dt.year
        df_monthly['month'] = df_monthly['next_month'].dt.month

        # Lọc và xử lý dữ liệu cần dùng
        df_filtered = df_monthly[
            [
                'date', 'year', 'month', 'ticker', 'exchangeCode', 'sectorL2', 'cap',
                'averageLiquidity21', 'averageLiquidity63', 'averageLiquidity252',
                'netIncomeQoQ', 'grossProfitQoQ', 'roe', 'eps', 'pe', 'pb'
            ]
        ].copy()

        current_period = pd.Period.now(freq='M')
        df_filtered = df_filtered[
            pd.to_datetime(df_filtered['year'].astype(str) + '-' + df_filtered['month'].astype(str)).dt.to_period(
                'M') <= current_period
            ]
        df_filtered = df_filtered.rename(columns={'ticker': 'symbol'})
        df_filtered = df_filtered.drop_duplicates()
        df_filtered = df_filtered.apply(lambda col: DataUtils.round_and_fix_near_zero_column(col))
        df_filtered = df_filtered.replace({np.inf: np.nan, -np.inf: np.nan})
        df_filtered = df_filtered.sort_values(by=['year', 'month', 'symbol']).reset_index(drop=True)
        df_filtered['date'] = df_filtered['date'].dt.strftime(SQLServerConsts.DATE_FORMAT)

        """
        FILTER 1: Lọc cơ bản về thanh khoản, vốn hóa, ngành và sàn giao dịch.
        """

        df_filtered = df_filtered.dropna(subset=['cap', 'grossProfitQoQ'])

        min_market_cap = 5e12 
        df_filtered = df_filtered[df_filtered['cap'] >= min_market_cap]

        min_avg_liquidity_63 = 1e4
        df_filtered = df_filtered[df_filtered['averageLiquidity63'] >= min_avg_liquidity_63]

        sectors = [
            'Banks',
            'Basic Resources',
            'Chemicals',
            'Construction & Materials',
            'Financial Services',
            'Food & Beverage',
            'Industrial Goods & Services',
            'Insurance',
            'Oil & Gas',
            'Personal & Household Goods',
            'Real Estate',
            'Telecommunications',
            'Travel & Leisure',
            'Utilities'
        ]
        df_filtered = df_filtered[df_filtered['sectorL2'].isin(sectors)]

        exchanges = ['HOSE', 'HNX']
        df_filtered = df_filtered[df_filtered['exchangeCode'].isin(exchanges)]

        """
        FILTER 2: Lọc theo tiêu chí Chất lượng.
        """

        # Loại bỏ các mã thiếu dữ liệu cho lớp lọc này
        df_filtered = df_filtered.dropna(subset=['roe', 'pe'])

        # Lọc theo ROE và D/E
        min_roe = 0.01
        max_pe = 30
        min_gross_profit_qoq = 0.01
        df_filtered = df_filtered[
            (df_filtered['roe'] >= min_roe) &
            (df_filtered['pe'] <= max_pe) &
            (df_filtered['grossProfitQoQ'] >= min_gross_profit_qoq)
        ]

        """
        FILTER 3: Xếp hạng các cổ phiếu còn lại và chọn ra 20 mã tốt nhất.
        """
        ranking_factors = {
            'roe': {'weight': 0.5, 'ascending': False},
            'grossProfitQoQ': {'weight': 0.5, 'ascending': False}
        }


        df_ranked = df_filtered.copy()
        df_ranked['CompositeScore'] = 0

        # Tính hạng cho từng yếu tố và cộng vào điểm tổng hợp theo trọng số
        for factor, props in ranking_factors.items():
            rank_col_name = f"{factor}Rank"
            df_ranked[rank_col_name] = df_ranked.groupby(['year', 'month'])[factor].rank(ascending=props['ascending'], method='first')
            df_ranked['CompositeScore'] += df_ranked[rank_col_name] * props['weight']

        final_df = pd.DataFrame()
        for year_month, group in df_ranked.groupby(['year', 'month']):
            top_stocks = group.nlargest(50, 'CompositeScore', keep='first')
            final_df = pd.concat([final_df, top_stocks], ignore_index=True)

        universe_top50_df = final_df[[
            'date', 'year', 'month', 'symbol', 'exchangeCode', 'sectorL2', 'cap',
            'averageLiquidity21', 'averageLiquidity63', 'averageLiquidity252',
            'grossProfitQoQ', 'roe', 'eps', 'pe', 'pb'
        ]]

        LOGGER.info("--- DONE FILTERING UNIVERSE TOP 50 ---\n")

        return universe_top50_df
