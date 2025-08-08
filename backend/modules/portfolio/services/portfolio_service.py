import pandas as pd
from typing import List
from pydantic import ValidationError

from backend.common.consts import SQLServerConsts, MessageConsts
from backend.common.responses.exceptions import BaseExceptionResponse
from backend.modules.base.query_builder import TextSQL
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
        df_stock_pivoted = df_stock_pivoted.dropna(axis=1, how="all")

        T = df_stock_pivoted.shape[0]
        tmp_year = pd.to_datetime(from_date).year
        tmp_month = pd.to_datetime(from_date).month
        assets = []
        portfolio_weights = []
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
                portfolio_id = PortfolioUtils.generate_general_portfolio_id(
                    date=end_of_period
                )

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
                    ),
                }
                portfolio_weights.append(record)

        portfolio_weights_df = pd.DataFrame(portfolio_weights)
        return portfolio_weights_df

    @classmethod
    async def create_custom_portfolio(
        cls,
        user_id: int,
        portfolio_name: str,
        symbols: List[str],
        max_positions: int = 30,
        days_back: int = 21,
    ) -> str:
        if len(symbols) > max_positions:
            raise BaseExceptionResponse(
                http_code=400,
                status_code=400,
                message=MessageConsts.BAD_REQUEST,
                errors=f"Maximum {max_positions} symbols allowed",
            )
        if len(symbols) < 2:
            raise BaseExceptionResponse(
                http_code=400,
                status_code=400,
                message=MessageConsts.BAD_REQUEST,
                errors="At least 2 symbols are required to create a portfolio",
            )

        df_stock_pivoted = await PriceDataProvider.get_price_data_pivoted()

        # Validate symbols exist
        await cls.validate_symbols(symbols, df_stock_pivoted)

        df_portfolio = df_stock_pivoted[symbols].copy()
        df_stock_pivoted = df_stock_pivoted.dropna(axis=1, how="all")
        # filter data with rows 21 days from the latest date
        if df_portfolio.empty:
            raise BaseExceptionResponse(
                http_code=404,
                status_code=404,
                message=MessageConsts.NOT_FOUND,
                errors="No stock data available",
            )
        latest_date = df_portfolio.index[-1]
        start_date = pd.to_datetime(latest_date) - pd.Timedelta(days=days_back)
        last_date = pd.to_datetime(latest_date)
        df_portfolio = df_portfolio.loc[start_date.strftime(SQLServerConsts.DATE_FORMAT) : last_date.strftime(SQLServerConsts.DATE_FORMAT)]

        x_CEMV, x_CEMV_neutralized, x_CEMV_limited, x_CEMV_neutralized_limit = (
            PortfolioOptimizer.optimize(df_portfolio=df_portfolio)
        )
        portfolio_id = PortfolioUtils.generate_custom_portfolio_id(
            user_id=user_id, portfolio_name=portfolio_name
        )

        portfolio_weights = []
        for j in range(len(x_CEMV)):
            record = {
                Portfolios.date.name: latest_date,
                Portfolios.symbol.name: df_portfolio.columns[j],
                Portfolios.portfolioId.name: portfolio_id,
                Portfolios.userId.name: user_id,
                Portfolios.portfolioType.name: "Custom",
                Portfolios.marketPrice.name: df_portfolio.iloc[-1, j],
                Portfolios.initialWeight.name: x_CEMV[j],
                Portfolios.neutralizedWeight.name: max(x_CEMV_neutralized[j], 0.0),
                Portfolios.limitedWeight.name: max(x_CEMV_limited[j], 0.0),
                Portfolios.neutralizedLimitedWeight.name: max(
                    x_CEMV_neutralized_limit[j], 0.0
                ),
            }
            portfolio_weights.append(record)

        portfolio_weights_df = pd.DataFrame(portfolio_weights)

        # Save portfolio weights to the database
        with cls.repo.session_scope() as session:
            temp_table = f"#{cls.repo.query_builder.table}"
            await cls.repo.upsert(
                temp_table=temp_table,
                records=portfolio_weights_df,
                identity_columns=["date", "symbol"],
                text_clauses={"__updatedAt__": TextSQL(SQLServerConsts.GMT_7_NOW_VARCHAR)},
            )
            session.commit()

        return True

    @classmethod
    async def validate_symbols(
        cls, symbols: List[str], df_stock_pivoted: pd.DataFrame
    ) -> None:
        """Validate that all symbols exist in the database."""
        if df_stock_pivoted.empty:
            raise BaseExceptionResponse(
                http_code=404,
                status_code=404,
                message=MessageConsts.NOT_FOUND,
                errors="No stock data available",
            )

        available_symbols = df_stock_pivoted.columns.tolist()

        try:
            for symbol in symbols:
                if symbol not in available_symbols:
                    raise BaseExceptionResponse(
                        http_code=404,
                        status_code=404,
                        message=MessageConsts.BAD_REQUEST,
                        errors=f"Symbol {symbol} not found in available stock data",
                    )
        except ValidationError as e:
            raise BaseExceptionResponse(
                http_code=400,
                status_code=400,
                message=MessageConsts.BAD_REQUEST,
                errors=str(e),
            )
