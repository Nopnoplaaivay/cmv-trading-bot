from typing import Dict

from backend.db.sessions import backend_session_scope
from backend.modules.base.query_builder import BaseQueryBuilder
from backend.modules.base.repositories import BaseRepo
from backend.modules.portfolio.entities import PortfolioMetadata

class PortfolioMetadataRepo(BaseRepo[Dict]):
    entity = PortfolioMetadata
    query_builder = BaseQueryBuilder(entity=entity)
    session_scope = backend_session_scope

    @classmethod
    async def get_by_portfolio_id(cls, portfolio_id: str) -> Dict:
        conditions = {cls.entity.portfolioId.name: portfolio_id}
        records = await cls.get_by_condition(conditions=conditions)
        return records
    
    @classmethod
    async def get_by_user_id(cls, user_id: int) -> Dict:
        conditions = {cls.entity.userId.name: user_id}
        records = await cls.get_by_condition(conditions=conditions)
        return records
