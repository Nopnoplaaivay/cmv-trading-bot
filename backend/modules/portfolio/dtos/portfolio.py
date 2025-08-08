from typing import List
from backend.modules.base.dto import BaseDTO


class CreateCustomPortfolioDTO(BaseDTO):
    portfolio_name: str
    symbols: List[str]