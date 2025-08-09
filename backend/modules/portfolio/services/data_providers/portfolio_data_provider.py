from typing import Optional, Dict

from backend.common.consts import TradingConsts
from backend.modules.portfolio.repositories import PortfoliosRepo
from backend.modules.portfolio.entities import Portfolios
from backend.modules.portfolio.utils.portfolio_utils import PortfolioUtils
from backend.utils.logger import LOGGER


class PortfolioDataProvider:
    repo = PortfoliosRepo

    @classmethod
    async def get_system_portfolio(
        cls, last_trading_date: str, next_trading_date: str
    ) -> Optional[Dict]:
        try:
            with cls.repo.session_scope() as session:
                portfolio_id = PortfolioUtils.generate_general_portfolio_id(date=last_trading_date)

                conditions = {
                    Portfolios.portfolioId.name: portfolio_id,
                    Portfolios.date.name: last_trading_date
                }
                records = await cls.repo.get_by_condition(conditions=conditions)

                if not records:
                    return None

                long_only_positions = []
                market_neutral_positions = []

                for record in records:
                    symbol = record[Portfolios.symbol.name]
                    initial_weight_pct = float(
                        record[Portfolios.initialWeight.name] * 100 or 0
                    )
                    neutralized_weight_pct = float(
                        record[Portfolios.neutralizedWeight.name] * 100 or 0
                    )

                    if initial_weight_pct >= 1:
                        long_only_positions.append(
                            {
                                "symbol": symbol,
                                "marketPrice": float(
                                    record[Portfolios.marketPrice.name]
                                ),
                                "weight": float(initial_weight_pct),
                            }
                        )

                    if neutralized_weight_pct >= 1:
                        market_neutral_positions.append(
                            {
                                "symbol": symbol,
                                "marketPrice": float(
                                    record[Portfolios.marketPrice.name]
                                ),
                                "weight": float(
                                    min(
                                        neutralized_weight_pct,
                                        TradingConsts.LIMIT_WEIGHT_PCT,
                                    )
                                ),
                            }
                        )

                long_only_positions.sort(key=lambda x: x["weight"], reverse=True)
                market_neutral_positions.sort(key=lambda x: x["weight"], reverse=True)
                session.commit()

            return {
                "date": next_trading_date,
                "long_only": long_only_positions,
                "market_neutral": market_neutral_positions,
            }

        except Exception as e:
            LOGGER.error(
                f"Error getting portfolio weights for {last_trading_date}: {e}"
            )
            return None
