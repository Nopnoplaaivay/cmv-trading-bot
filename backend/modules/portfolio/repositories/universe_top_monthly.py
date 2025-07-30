from typing import Dict

from backend.db.sessions import backend_session_scope
from backend.modules.base.query_builder import BaseQueryBuilder
from backend.modules.base.repositories import BaseRepo
from backend.modules.portfolio.entities import UniverseTopMonthly


class UniverseTopMonthlyRepo(BaseRepo[Dict]):
    entity = UniverseTopMonthly
    query_builder = BaseQueryBuilder(entity=entity)
    session_scope = backend_session_scope

    @classmethod
    async def get_asset_by_year_month(cls, year, month):
        with cls.session_scope() as session:
            conditions = {
                cls.entity.year.name: year,
                cls.entity.month.name: month,
            }
            records = await cls.get_by_condition(conditions=conditions)
            session.commit()
        return records