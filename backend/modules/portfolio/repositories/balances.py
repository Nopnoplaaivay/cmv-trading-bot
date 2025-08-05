from typing import Dict, Optional

from backend.db.sessions import backend_session_scope
from backend.modules.base.query_builder import BaseQueryBuilder
from backend.modules.base.repositories import BaseRepo
from backend.modules.portfolio.entities import Balances


class BalancesRepo(BaseRepo[Dict]):
    entity = Balances
    query_builder = BaseQueryBuilder(entity=entity)
    session_scope = backend_session_scope

    @classmethod
    async def get_by_account_id(cls, account_id: str) -> Optional[Dict]:
        conditions = {cls.entity.accountId.name: account_id}
        results = await cls.get_by_condition(conditions=conditions)
        return results[0] if results else None
