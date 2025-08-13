from typing import Optional, Dict

from backend.common.consts import TradingConsts
from backend.modules.portfolio.repositories import PortfoliosRepo
from backend.modules.portfolio.entities import Portfolios
from backend.modules.portfolio.utils.portfolio_utils import PortfolioUtils
from backend.utils.logger import LOGGER


class PortfolioDataProvider:
    repo = PortfoliosRepo

    @classmethod
    async def get_portfolio_weights_by_id(cls, portfolio_id) -> Optional[Dict]:
        try:
            with cls.repo.session_scope() as session:
                conditions = {Portfolios.portfolioId.name: portfolio_id}
                records = await cls.repo.get_by_condition(conditions=conditions)

                if not records:
                    return None

                latest_date = max(record[Portfolios.date.name] for record in records)
                portfolios = [
                    record
                    for record in records
                    if (
                        record[Portfolios.portfolioId.name] == portfolio_id
                        and record[Portfolios.date.name] == latest_date
                    )
                ]

                long_only_positions = []
                market_neutral_positions = []

                for position in portfolios:
                    symbol = position[Portfolios.symbol.name]
                    initial_weight_pct = float(
                        position[Portfolios.initialWeight.name] * 100 or 0
                    )
                    neutralized_weight_pct = float(
                        position[Portfolios.neutralizedWeight.name] * 100 or 0
                    )

                    if initial_weight_pct >= 1:
                        long_only_positions.append(
                            {
                                "symbol": symbol,
                                "marketPrice": float(
                                    position[Portfolios.marketPrice.name]
                                ),
                                "weight": float(initial_weight_pct),
                            }
                        )

                    if neutralized_weight_pct >= 1:
                        market_neutral_positions.append(
                            {
                                "symbol": symbol,
                                "marketPrice": float(
                                    position[Portfolios.marketPrice.name]
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
                "date": latest_date,
                "LongOnly": long_only_positions,
                "MarketNeutral": market_neutral_positions,
            }

        except Exception as e:
            LOGGER.error(f"Error getting portfolio weights: {e}")
            return None
