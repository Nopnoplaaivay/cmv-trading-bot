from typing import Dict

from backend.db.sessions import backend_session_scope
from backend.modules.base.query_builder import BaseQueryBuilder
from backend.modules.base.repositories import BaseRepo
from backend.modules.portfolio.entities import Portfolios


class PortfoliosRepo(BaseRepo[Dict]):
    entity = Portfolios
    query_builder = BaseQueryBuilder(entity=entity)
    session_scope = backend_session_scope

    @classmethod
    async def get_by_portfolio_id(cls, portfolio_id: str) -> Dict:
        with cls.session_scope() as session:
            conditions = {cls.entity.portfolioId.name: portfolio_id}
            records = await cls.get_by_condition(conditions=conditions)
            session.commit()
        return records
    
    @classmethod
    async def get_by_user_id(cls, user_id: int) -> Dict:
        with cls.session_scope() as session:
            conditions = {cls.entity.userId.name: user_id}
            records = await cls.get_by_condition(conditions=conditions)
            session.commit()
        return records