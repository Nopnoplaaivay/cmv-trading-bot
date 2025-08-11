import datetime
import warnings
import pandas as pd
from typing import List
from pydantic import ValidationError

from backend.common.consts import SQLServerConsts, MessageConsts
from backend.common.responses.exceptions import BaseExceptionResponse
from backend.modules.auth.types.auth import JwtPayload
from backend.modules.base.query_builder import TextSQL
from backend.modules.base_daily import BaseDailyService
from backend.modules.portfolio.entities import (
    StocksUniverse,
    Portfolios,
    PortfolioMetadata,
)
from backend.modules.portfolio.repositories import (
    PortfoliosRepo,
    PortfolioMetadataRepo,
    StocksUniverseRepo,
    portfolio,
)
from backend.modules.portfolio.core import PortfolioOptimizer
from backend.modules.portfolio.services.data_providers import PriceDataProvider
from backend.modules.portfolio.services.processors import PortfolioCalculator
from backend.modules.portfolio.utils.portfolio_utils import PortfolioUtils
from backend.modules.portfolio.infrastructure import TradingCalendarService


class PortfoliosService(BaseDailyService):
    repo = PortfoliosRepo
    metadata_repo = PortfolioMetadataRepo
    trading_calendar = TradingCalendarService
    portfolio_optimizer = PortfolioOptimizer
    portfolio_calculator = PortfolioCalculator

    @classmethod
    async def update_data(cls, from_date: str) -> pd.DataFrame:
        days_back = 21

        df_stock_pivoted = await PriceDataProvider(prefix="STOCK").get_market_data(
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
            end_of_period = window.index[-1]

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
                cls.portfolio_optimizer.optimize(df_portfolio=df_portfolio)
            )

            for j in range(len(x_CEMV)):
                record = {
                    Portfolios.date.name: end_of_period,
                    Portfolios.symbol.name: df_portfolio.columns[j],
                    Portfolios.portfolioId.name: portfolio_id,
                    Portfolios.marketPrice.name: df_portfolio.iloc[-1, j],
                    Portfolios.initialWeight.name: x_CEMV[j],
                    Portfolios.neutralizedWeight.name: max(x_CEMV_neutralized[j], 0.0),
                    Portfolios.limitedWeight.name: float(0),
                    Portfolios.neutralizedLimitedWeight.name: float(0),
                }
                portfolio_weights.append(record)

        portfolio_weights_df = pd.DataFrame(portfolio_weights)
        return portfolio_weights_df

    @classmethod
    async def create_portfolio(
        cls,
        user_id: int,
        portfolio_name: str,
        portfolio_desc: str,
        symbols: List[str],
        max_positions: int = 30,
        days_back: int = 21,
    ) -> str:
        try:
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

            df_stock_pivoted = await PriceDataProvider(prefix="STOCK").get_market_data()

            # Validate symbols exist
            await cls.validate_symbols(
                symbols=symbols, df_stock_pivoted=df_stock_pivoted
            )

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
            df_portfolio = df_portfolio.loc[
                start_date.strftime(SQLServerConsts.DATE_FORMAT) : last_date.strftime(
                    SQLServerConsts.DATE_FORMAT
                )
            ]

            x_CEMV, x_CEMV_neutralized, x_CEMV_limited, x_CEMV_neutralized_limit = (
                cls.portfolio_optimizer.optimize(df_portfolio=df_portfolio)
            )
            portfolio_id = PortfolioUtils.generate_custom_portfolio_id(
                user_id=user_id, portfolio_name=portfolio_name
            )

            # Get portfolio weights
            portfolio_weights = []
            for j in range(len(x_CEMV)):
                record = {
                    Portfolios.date.name: latest_date,
                    Portfolios.symbol.name: df_portfolio.columns[j],
                    Portfolios.portfolioId.name: portfolio_id,
                    Portfolios.marketPrice.name: df_portfolio.iloc[-1, j],
                    Portfolios.initialWeight.name: x_CEMV[j],
                    Portfolios.neutralizedWeight.name: max(x_CEMV_neutralized[j], 0.0),
                    Portfolios.limitedWeight.name: float(0),
                    Portfolios.neutralizedLimitedWeight.name: float(0),
                }
                portfolio_weights.append(record)
            portfolio_weights_df = pd.DataFrame(portfolio_weights)

            # Save portfolio weights to db
            with cls.repo.session_scope() as session:
                await cls.metadata_repo.insert(
                    record={
                        PortfolioMetadata.portfolioId.name: portfolio_id,
                        PortfolioMetadata.userId.name: user_id,
                        PortfolioMetadata.portfolioName.name: portfolio_name,
                        PortfolioMetadata.portfolioType.name: "Custom",
                        PortfolioMetadata.portfolioDesc.name: portfolio_desc,
                        PortfolioMetadata.algorithm.name: "CMV",
                    },
                    returning=False,
                )
                temp_table = f"#{cls.repo.query_builder.table}"
                await cls.repo.upsert(
                    temp_table=temp_table,
                    records=portfolio_weights_df,
                    identity_columns=["date", "symbol"],
                    text_clauses={
                        "__updatedAt__": TextSQL(SQLServerConsts.GMT_7_NOW_VARCHAR)
                    },
                )
                session.commit()

            return {"message": f"Portfolio {portfolio_id} created successfully"}
        except Exception as e:
            raise BaseExceptionResponse(
                http_code=500,
                status_code=500,
                message=MessageConsts.INTERNAL_SERVER_ERROR,
                errors=str(e),
            )

    @classmethod
    async def update_portfolio_symbols(
        cls, portfolio_id: str, symbols: List[str], user: JwtPayload
    ) -> None:
        try:
            # First validate that the portfolio exists
            with cls.repo.session_scope() as session:
                records = await cls.metadata_repo.get_by_portfolio_id(
                    portfolio_id=portfolio_id
                )
                if len(records) == 0:
                    raise BaseExceptionResponse(
                        http_code=404,
                        status_code=404,
                        message=MessageConsts.NOT_FOUND,
                        errors=f"Portfolio with ID {portfolio_id} not found",
                    )

                existing_portfolio = records[0]
                await cls.repo.delete_by_portfolio_id(portfolio_id=portfolio_id)

                # Get price data for optimization
                df_stock_pivoted = await PriceDataProvider(
                    prefix="STOCK"
                ).get_market_data()
                await cls.validate_symbols(
                    symbols=symbols, df_stock_pivoted=df_stock_pivoted
                )
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
                days_back = 21  # temporary
                start_date = pd.to_datetime(latest_date) - pd.Timedelta(days=days_back)
                last_date = pd.to_datetime(latest_date)
                df_portfolio = df_portfolio.loc[
                    start_date.strftime(
                        SQLServerConsts.DATE_FORMAT
                    ) : last_date.strftime(SQLServerConsts.DATE_FORMAT)
                ]

                x_CEMV, x_CEMV_neutralized, x_CEMV_limited, x_CEMV_neutralized_limit = (
                    cls.portfolio_optimizer.optimize(df_portfolio=df_portfolio)
                )
                portfolio_id = existing_portfolio[PortfolioMetadata.portfolioId.name]

                # Get portfolio weights
                portfolio_weights = []
                for j in range(len(x_CEMV)):
                    record = {
                        Portfolios.date.name: latest_date,
                        Portfolios.symbol.name: df_portfolio.columns[j],
                        Portfolios.portfolioId.name: portfolio_id,
                        Portfolios.marketPrice.name: df_portfolio.iloc[-1, j],
                        Portfolios.initialWeight.name: x_CEMV[j],
                        Portfolios.neutralizedWeight.name: max(
                            x_CEMV_neutralized[j], 0.0
                        ),
                        Portfolios.limitedWeight.name: float(0),
                        Portfolios.neutralizedLimitedWeight.name: float(0),
                    }
                    portfolio_weights.append(record)

                if len(portfolio_weights) == 0:
                    raise BaseExceptionResponse(
                        http_code=400,
                        status_code=400,
                        message=MessageConsts.BAD_REQUEST,
                        errors="No valid portfolio weights calculated for the given symbols",
                    )

                # Insert new records using insert_many
                await cls.repo.insert_many(portfolio_weights, returning=False)

                # Update portfolio metadata
                await cls.metadata_repo.update(
                    record={PortfolioMetadata.portfolioId.name: portfolio_id},
                    identity_columns=[PortfolioMetadata.portfolioId.name],
                    returning=False,
                    text_clauses={
                        "__updatedAt__": TextSQL(SQLServerConsts.GMT_7_NOW_VARCHAR)
                    },
                )
                session.commit()

                return {"message": f"Portfolio {portfolio_id} updated successfully"}

        except Exception as e:
            raise BaseExceptionResponse(
                http_code=500,
                status_code=500,
                message=MessageConsts.INTERNAL_SERVER_ERROR,
                errors=f"Failed to update portfolio: {str(e)}",
            )

    @classmethod
    async def get_portfolio_by_id(
        cls, portfolio_id: str, user: JwtPayload
    ) -> pd.DataFrame:
        try:
            with cls.repo.session_scope() as session:
                portfolio = await cls.repo.get_by_portfolio_id(
                    portfolio_id=portfolio_id
                )
                if not portfolio:
                    raise BaseExceptionResponse(
                        http_code=404,
                        status_code=404,
                        message=MessageConsts.NOT_FOUND,
                        errors=f"Portfolio {portfolio_id} not found",
                    )

                portfolios_metadata = await cls.metadata_repo.get_by_portfolio_id(
                    portfolio_id=portfolio_id
                )
                if not portfolios_metadata:
                    raise BaseExceptionResponse(
                        http_code=404,
                        status_code=404,
                        message=MessageConsts.NOT_FOUND,
                        errors=f"No portfolios found for user {user.userId}",
                    )
                session.commit()

            user_id = portfolios_metadata[0][PortfolioMetadata.userId.name]
            if user_id != user.userId:
                raise BaseExceptionResponse(
                    http_code=403,
                    status_code=403,
                    message=MessageConsts.FORBIDDEN,
                    errors=f"User {user.userId} is not allowed to access portfolio {portfolio_id}",
                )

            return {"records": portfolio}
        except Exception as e:
            raise BaseExceptionResponse(
                http_code=500,
                status_code=500,
                message=MessageConsts.INTERNAL_SERVER_ERROR,
                errors=str(e),
            )

    @classmethod
    async def get_portfolios_by_user_id(cls, user: JwtPayload) -> pd.DataFrame:
        try:
            with cls.repo.session_scope() as session:
                portfolios_metadata = await cls.metadata_repo.get_by_user_id(
                    user_id=user.userId
                )
                if not portfolios_metadata:
                    return {"portfolios": []}
                unique_portfolio_ids = set(
                    metadata[PortfolioMetadata.portfolioId.name]
                    for metadata in portfolios_metadata
                )

                condition_str = "'" + "','".join(unique_portfolio_ids) + "'"
                sql_query = f"""
                    SET TRANSACTION ISOLATION LEVEL READ UNCOMMITTED;

                    WITH UncommittedData AS (
                        SELECT *
                        FROM [BotPortfolio].[portfolios]
                        WHERE [portfolioId] IN ({condition_str})
                    )

                    SELECT *
                    FROM UncommittedData
                """

                with warnings.catch_warnings():
                    warnings.simplefilter("ignore", UserWarning)
                    conn = session.connection().connection
                    df_portfolios = pd.read_sql_query(sql_query, conn)

                session.commit()

            # convert to list of portfolios
            portfolios_records = df_portfolios.to_dict(orient="records")
            if not portfolios_records:
                return {"portfolios": []}

            portfolios = []
            for portfolio_id in unique_portfolio_ids:
                portfolio_metadata = next(
                    (
                        meta
                        for meta in portfolios_metadata
                        if meta[Portfolios.portfolioId.name] == portfolio_id
                    ),
                    None,
                )
                if portfolio_metadata:
                    portfolios.append(
                        {
                            "portfolioId": portfolio_id,
                            "metadata": portfolio_metadata,
                            "records": [
                                port
                                for port in portfolios_records
                                if port[Portfolios.portfolioId.name] == portfolio_id
                            ],
                        }
                    )
            return {"portfolios": portfolios}

        except Exception as e:
            raise BaseExceptionResponse(
                http_code=500,
                status_code=500,
                message=MessageConsts.INTERNAL_SERVER_ERROR,
                errors=str(e),
            )

    @classmethod
    async def delete_portfolio(cls, portfolio_id: str) -> None:
        try:
            with cls.repo.session_scope() as session:
                existing_portfolio = await cls.metadata_repo.get_by_portfolio_id(
                    portfolio_id=portfolio_id
                )
                if not existing_portfolio:
                    raise BaseExceptionResponse(
                        http_code=404,
                        status_code=404,
                        message=MessageConsts.NOT_FOUND,
                        errors=f"No portfolio found with id {portfolio_id}",
                    )

                await cls.repo.delete_by_portfolio_id(portfolio_id=portfolio_id)
                await cls.metadata_repo.delete_by_portfolio_id(
                    portfolio_id=portfolio_id
                )
                session.commit()
            return {"message": f"Portfolio {portfolio_id} deleted successfully"}
        except Exception as e:
            raise BaseExceptionResponse(
                http_code=500,
                status_code=500,
                message=MessageConsts.INTERNAL_SERVER_ERROR,
                errors=str(e),
            )

    @classmethod
    async def get_available_symbols(cls) -> pd.DataFrame:
        try:
            df_stock_pivoted = await PriceDataProvider(prefix="STOCK").get_market_data()
            # df_stock_pivoted = df_stock_pivoted.dropna(axis=1, how="all")
            if df_stock_pivoted.empty:
                raise BaseExceptionResponse(
                    http_code=404,
                    status_code=404,
                    message=MessageConsts.NOT_FOUND,
                    errors="No stock data available",
                )

            available_symbols = df_stock_pivoted.columns.tolist()

            return {"records": available_symbols}
        except Exception as e:
            raise BaseExceptionResponse(
                http_code=500,
                status_code=500,
                message=MessageConsts.INTERNAL_SERVER_ERROR,
                errors=str(e),
            )

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

    @classmethod
    async def get_portfolio_pnl(
        cls, portfolio_id: str, strategy: str = "long-only"
    ) -> dict:
        try:
            with cls.repo.session_scope() as session:
                portfolio_metadata = await cls.metadata_repo.get_by_portfolio_id(
                    portfolio_id=portfolio_id
                )
                if not portfolio_metadata:
                    raise BaseExceptionResponse(
                        http_code=404,
                        status_code=404,
                        message=MessageConsts.NOT_FOUND,
                        errors=f"No portfolio metadata found with id {portfolio_id}",
                    )

                days_back = 21

                last_trading_date, _ = (
                    cls.trading_calendar.get_last_next_trading_dates()
                )
                # Calculate from_date as last trading date minus 1 year minus days_back
                from_date = last_trading_date - datetime.timedelta(days=365 + days_back)
                from_date_str = from_date.strftime(SQLServerConsts.DATE_FORMAT)

                portfolios = await cls.repo.get_by_condition(
                    conditions={Portfolios.portfolioId.name: portfolio_id}
                )
                if not portfolios:
                    raise BaseExceptionResponse(
                        http_code=404,
                        status_code=404,
                        message=MessageConsts.NOT_FOUND,
                        errors=f"No portfolio found with id {portfolio_id}",
                    )

                symbols = list(
                    set([record[Portfolios.symbol.name] for record in portfolios])
                )
                df_stock_pivoted = await PriceDataProvider(
                    prefix="STOCK"
                ).get_market_data(from_date=from_date_str)
                df_index = await PriceDataProvider(prefix="INDEX").get_market_data(
                    from_date=from_date_str
                )
                df_portfolio = df_stock_pivoted[symbols].copy()

                portfolio_weights_df = []
                T = df_portfolio.shape[0]
                n_assets = df_portfolio.shape[1]
                for i in range(days_back - 1, T):
                    window = df_portfolio.iloc[i - days_back + 1 : i + 1, :]
                    end_of_period = window.index[-1]
                    prices = window.iloc[-1].values
                    x_CEMV, x_CEMV_neutralized, _, _ = cls.portfolio_optimizer.optimize(
                        df_portfolio=window
                    )
                    weights = x_CEMV if strategy == "long-only" else x_CEMV_neutralized

                    for j in range(n_assets):
                        record = {
                            "date": end_of_period,
                            "symbol": symbols[j],
                            "weight": weights[j],
                            "price": prices[j],
                        }
                        portfolio_weights_df.append(record)

                portfolio_weights_df = pd.DataFrame(portfolio_weights_df)
                portfolio_pnl_df = cls.portfolio_calculator.process_portfolio_pnl(
                    portfolio_weights_df=portfolio_weights_df
                )
                index_pnl_df = cls.portfolio_calculator.process_index_pnl(
                    df_index=df_index
                )

                # Check and synchronize dates between portfolio and index PnL using forward fill
                portfolio_dates = set(portfolio_pnl_df["date"].tolist())
                index_dates = set(index_pnl_df["date"].tolist())

                print(f"Portfolio PnL dates count: {len(portfolio_dates)}")
                print(f"Index PnL dates count: {len(index_dates)}")

                all_dates = sorted(list(portfolio_dates.union(index_dates)))
                missing_in_portfolio = index_dates - portfolio_dates
                missing_in_index = portfolio_dates - index_dates

                print(f"Total unique dates: {len(all_dates)}")
                if missing_in_portfolio:
                    print(
                        f"Dates missing in portfolio: {len(missing_in_portfolio)} days"
                    )
                if missing_in_index:
                    print(f"Dates missing in index: {len(missing_in_index)} days")

                # Create complete date range and forward fill missing values
                if all_dates:
                    # Convert date columns to datetime for proper sorting
                    portfolio_pnl_df["date"] = pd.to_datetime(portfolio_pnl_df["date"])
                    index_pnl_df["date"] = pd.to_datetime(index_pnl_df["date"])

                    # Create complete date range DataFrame
                    complete_dates_df = pd.DataFrame(
                        {"date": pd.to_datetime(all_dates)}
                    )

                    # Merge and forward fill portfolio data
                    portfolio_complete = complete_dates_df.merge(
                        portfolio_pnl_df, on="date", how="left"
                    )
                    portfolio_complete["pnl_pct"] = portfolio_complete[
                        "pnl_pct"
                    ].ffill()
                    # If first values are NaN, fill with 0
                    portfolio_complete["pnl_pct"] = portfolio_complete[
                        "pnl_pct"
                    ].fillna(0)

                    # Merge and forward fill index data
                    index_complete = complete_dates_df.merge(
                        index_pnl_df, on="date", how="left"
                    )
                    index_complete["pnl_pct"] = index_complete["pnl_pct"].ffill()
                    # If first values are NaN, fill with 0
                    index_complete["pnl_pct"] = index_complete["pnl_pct"].fillna(0)
                    index_complete["pnl_pct"] = index_complete["pnl_pct"].fillna(0)

                    # Convert back to string format for response
                    portfolio_complete["date"] = portfolio_complete["date"].dt.strftime(
                        SQLServerConsts.DATE_FORMAT
                    )
                    index_complete["date"] = index_complete["date"].dt.strftime(
                        SQLServerConsts.DATE_FORMAT
                    )

                    portfolio_pnl_df = portfolio_complete
                    index_pnl_df = index_complete

                else:
                    print("WARNING: No dates found in either portfolio or index!")
                    portfolio_pnl_df = pd.DataFrame(columns=["date", "pnl_pct"])
                    index_pnl_df = pd.DataFrame(columns=["date", "pnl_pct"])

                # Format response for easy frontend chart plotting
                pnl_data = {
                    "portfolio": portfolio_pnl_df.to_dict("records"),
                    "vnindex": index_pnl_df.to_dict("records"),
                    "metadata": {
                        "portfolio_id": portfolio_id,
                        "strategy": strategy,
                        "from_date": from_date_str,
                        "to_date": last_trading_date.strftime(
                            SQLServerConsts.DATE_FORMAT
                        ),
                        "total_portfolio_days": len(portfolio_pnl_df),
                        "total_index_days": len(index_pnl_df),
                        "total_dates": len(all_dates) if all_dates else 0,
                        "missing_in_portfolio": len(missing_in_portfolio),
                        "missing_in_index": len(missing_in_index),
                        "symbols": symbols,
                    },
                }

                return pnl_data
        except Exception as e:
            raise BaseExceptionResponse(
                http_code=500,
                status_code=500,
                message=MessageConsts.INTERNAL_SERVER_ERROR,
                errors=str(e),
            )
