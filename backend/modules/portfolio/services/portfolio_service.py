import pandas as pd
import warnings

from backend.common.consts import SQLServerConsts
from backend.db.sessions import mart_session_scope
from backend.modules.base_daily import BaseDailyService
from backend.modules.portfolio.entities import StocksUniverse, Portfolios
from backend.modules.portfolio.repositories import (
    PortfoliosRepo,
    StocksUniverseRepo,
)
from backend.modules.portfolio.core import PortfolioOptimizer
from backend.modules.portfolio.services.data_providers import PriceDataProvider
from backend.modules.portfolio.utils.portfolio_utils import PortfolioUtils


class PortfoliosService(BaseDailyService):
    repo = PortfoliosRepo

    @classmethod
    async def update_data(cls, from_date: str) -> pd.DataFrame:
        days_back = 21

        df_stock_pivoted = await PriceDataProvider.get_price_data_pivoted(
            from_date=from_date, days_back=days_back
        )

        T = df_stock_pivoted.shape[0]
        tmp_year = pd.to_datetime(from_date).year
        tmp_month = pd.to_datetime(from_date).month
        assets = []
        optimized_weights = []
        portfolio_id = PortfolioUtils.generate_general_portfolio_id(date=from_date)

        for i in range(days_back - 1, T):
            window = df_stock_pivoted.iloc[i - days_back + 1 : i + 1]
            end_of_period = window.index[-1]  # Use index instead of column 'date'

            # Check if need to update the assets for the current month
            if (
                pd.to_datetime(end_of_period).year != tmp_year
                or pd.to_datetime(end_of_period).month != tmp_month
                or not assets
            ):
                tmp_year = pd.to_datetime(end_of_period).year
                tmp_month = pd.to_datetime(end_of_period).month
                portfolio_id = PortfolioUtils.generate_general_portfolio_id(date=end_of_period)

                records = await StocksUniverseRepo.get_asset_by_year_month(
                    year=tmp_year, month=tmp_month
                )
                assets = [record[StocksUniverse.symbol.name] for record in records]

            # Filter columns (tickers) that are in the current month's universe
            available_assets = [asset for asset in assets if asset in window.columns]
            df_portfolio = window[available_assets].copy()
            x_CEMV, x_CEMV_neutralized, x_CEMV_limited, x_CEMV_neutralized_limit = (
                PortfolioOptimizer.optimize(df_portfolio=df_portfolio)
            )

            for j in range(len(x_CEMV)):
                record = {
                    Portfolios.date.name: end_of_period,
                    Portfolios.symbol.name: df_portfolio.columns[j],
                    Portfolios.portfolioId.name: portfolio_id,
                    Portfolios.marketPrice.name: df_portfolio.iloc[-1, j],
                    Portfolios.initialWeight.name: x_CEMV[j],
                    Portfolios.neutralizedWeight.name: max(x_CEMV_neutralized[j], 0.0),
                    Portfolios.limitedWeight.name: max(x_CEMV_limited[j], 0.0),
                    Portfolios.neutralizedLimitedWeight.name: max(
                        x_CEMV_neutralized_limit[j], 0.0
                    )
                }
                optimized_weights.append(record)

        optimized_weights_df = pd.DataFrame(optimized_weights)
        return optimized_weights_df
