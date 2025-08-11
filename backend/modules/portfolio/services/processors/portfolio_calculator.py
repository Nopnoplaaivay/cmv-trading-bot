import pandas as pd
import numpy as np
from decimal import Decimal
from typing import List, Dict, Optional

from backend.common.consts import SQLServerConsts


class PortfolioCalculator:
    @staticmethod
    def process_portfolio_pnl(portfolio_weights_df: pd.DataFrame) -> pd.DataFrame:
        BOOK_SIZE = 1e9  # 1 tỷ VND
        portfolio_data = portfolio_weights_df.copy()

        if portfolio_data.empty:
            return pd.DataFrame(columns=["date", "pnl_pct"])

        # Sort by date to ensure proper order
        portfolio_data["date"] = pd.to_datetime(portfolio_data["date"])
        portfolio_data = portfolio_data.sort_values(["date", "symbol"])

        # Get unique dates and symbols
        dates = portfolio_data["date"].unique()
        symbols = portfolio_data["symbol"].unique()

        # Create pivot tables for easier calculation
        weights_pivot = portfolio_data.pivot(
            index="date", columns="symbol", values="weight"
        ).fillna(0)
        prices_pivot = portfolio_data.pivot(
            index="date", columns="symbol", values="price"
        ).ffill()

        # Initialize portfolio value tracking
        portfolio_values = []
        current_portfolio_value = BOOK_SIZE

        for i, date in enumerate(dates):
            if i == 0 or i == 1:
                # First day - just use base value
                portfolio_values.append(BOOK_SIZE)
            else:
                # Get previous weights and current prices
                prev_date = dates[i - 2]
                prev_weights = weights_pivot.loc[prev_date].values
                prev_prices = prices_pivot.loc[prev_date].values
                curr_prices = prices_pivot.loc[date].values

                # Calculate price returns, handle NaN/inf
                price_returns = (curr_prices - prev_prices) / prev_prices
                price_returns = np.nan_to_num(
                    price_returns, nan=0.0, posinf=0.0, neginf=0.0
                )

                # Calculate portfolio return using previous weights
                portfolio_return = np.sum(prev_weights * price_returns)

                # Update portfolio value
                current_portfolio_value *= 1 + portfolio_return
                portfolio_values.append(current_portfolio_value)

        # Create result DataFrame
        result_df = pd.DataFrame({"date": dates, "portfolio_value": portfolio_values})

        # Calculate PnL percentage
        result_df["pnl_pct"] = (result_df["portfolio_value"] / BOOK_SIZE - 1) * 100

        # Format date
        result_df["date"] = result_df["date"].dt.strftime(SQLServerConsts.DATE_FORMAT)

        return result_df[["date", "pnl_pct"]]

    @staticmethod
    def process_index_pnl(df_index: pd.DataFrame) -> pd.DataFrame:
        BOOK_SIZE = 1e9
        index_data = df_index.copy()

        if index_data.empty:
            return pd.DataFrame(columns=["date", "pnl_pct"])

        # Sort by date to ensure proper order
        index_data["date"] = pd.to_datetime(index_data["date"])
        index_data = index_data.sort_values("date")

        # Initialize index value tracking
        index_values = []
        current_index_value = BOOK_SIZE

        for i in range(len(index_data)):
            if i == 0 or i == 1:
                # First day - just use base value
                index_values.append(BOOK_SIZE)
            else:
                # Get previous and current index prices
                prev_price = index_data["closeIndex"].iloc[i - 2]
                curr_price = index_data["closeIndex"].iloc[i]

                # Calculate price return
                if prev_price > 0:
                    price_return = (curr_price - prev_price) / prev_price
                else:
                    price_return = 0.0

                # Handle NaN/inf
                price_return = np.nan_to_num(
                    price_return, nan=0.0, posinf=0.0, neginf=0.0
                )

                # Update index value
                current_index_value *= 1 + price_return
                index_values.append(current_index_value)

        # Create result DataFrame
        result_df = pd.DataFrame(
            {"date": index_data["date"], "index_value": index_values}
        )

        # Calculate PnL percentage
        result_df["pnl_pct"] = (result_df["index_value"] / BOOK_SIZE - 1) * 100

        # Format date
        result_df["date"] = result_df["date"].dt.strftime(SQLServerConsts.DATE_FORMAT)

        return result_df[["date", "pnl_pct"]]
