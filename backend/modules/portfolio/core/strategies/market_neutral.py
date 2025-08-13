from typing import Dict, List
from backend.modules.portfolio.core.strategies.base import BasePortfolioStrategy


class MarketNeutralStrategy(BasePortfolioStrategy):
    def get_target_weights(self, portfolio_data: Dict) -> List[Dict]:
        return portfolio_data.get("MarketNeutral", [])