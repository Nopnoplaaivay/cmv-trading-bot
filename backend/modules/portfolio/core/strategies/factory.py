from backend.modules.portfolio.core.strategies.base import BasePortfolioStrategy
from backend.modules.portfolio.core.strategies.long_only import LongOnlyStrategy
from backend.modules.portfolio.core.strategies.market_neutral import MarketNeutralStrategy


class StrategyFactory:
    @staticmethod
    def create_strategy(strategy_type: str) -> BasePortfolioStrategy:
        strategies = {
            "long_only": LongOnlyStrategy(),
            "market_neutral": MarketNeutralStrategy(),
        }
        if strategy_type not in strategies:
            raise ValueError(f"Unknown strategy type: {strategy_type}")
        return strategies[strategy_type]
