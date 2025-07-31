from abc import ABC, abstractmethod
from typing import Optional

from backend.modules.dnse.entities import TradingTokens



class BaseTokenStorage(ABC):
    @abstractmethod
    async def save_token(self, token_data: TradingTokens) -> None:
        pass
    
    @abstractmethod
    async def load_token(self, account: str, broker: str = 'DNSE') -> Optional[TradingTokens]:
        pass
    
    @abstractmethod
    async def delete_token(self, account: str, broker: str = 'DNSE') -> None:
        pass
    
    @abstractmethod
    async def cleanup(self) -> None:
        pass