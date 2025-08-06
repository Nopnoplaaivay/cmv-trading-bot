from typing import Dict, List, Optional

from backend.db.sessions import backend_session_scope
from backend.modules.base.query_builder import BaseQueryBuilder
from backend.modules.base.repositories import BaseRepo
from backend.modules.portfolio.entities import Accounts


class AccountsRepo(BaseRepo[Dict]):
    entity = Accounts
    query_builder = BaseQueryBuilder(entity=entity)
    session_scope = backend_session_scope

    @classmethod
    async def get_by_user_id(cls, user_id: int) -> List[Dict]:
        """Get all accounts for a specific user."""
        conditions = {cls.entity.userId.name: user_id}
        return await cls.get_by_condition(conditions=conditions)

    @classmethod
    async def get_accounts_by_username(cls, custody_code: str) -> Optional[Dict]:
        with cls.session_scope() as session:
            conditions = {cls.entity.custodyCode.name: custody_code}
            records = await cls.get_by_condition(conditions=conditions)
            session.commit()

        return records if records else None
    
    @classmethod
    async def get_by_broker_account_id(cls, broker_account_id: str) -> Optional[Dict]:
        """Get account by broker account ID."""
        with cls.session_scope() as session:
            conditions = {cls.entity.brokerAccountId.name: broker_account_id}
            records = await cls.get_by_condition(conditions=conditions)
            session.commit()

        return records if records else None
