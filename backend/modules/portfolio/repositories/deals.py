from typing import Dict, List, Optional

from backend.db.sessions import backend_session_scope
from backend.modules.base.query_builder import BaseQueryBuilder
from backend.modules.base.repositories import BaseRepo
from backend.modules.portfolio.entities import Deals


class DealsRepo(BaseRepo[Dict]):
    entity = Deals
    query_builder = BaseQueryBuilder(entity=entity)
    session_scope = backend_session_scope

    @classmethod
    async def get_deals_by_broker_account_id(
        cls, broker_account_id: str
    ) -> List[Dict]:
        with cls.session_scope() as session:
            conditions = {cls.entity.brokerAccountId.name: broker_account_id}
            results = await cls.get_by_condition(conditions=conditions)
            # Ensure the session is used for the query
            session.commit()
        return results