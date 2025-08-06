from abc import ABC, abstractmethod
from typing import Dict, List


class BasePortfolioStrategy(ABC):
    @abstractmethod
    def get_target_weights(self, portfolio_data: Dict) -> List[Dict]:
        pass
