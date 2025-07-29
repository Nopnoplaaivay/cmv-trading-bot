from typing import Dict

from backend.db.sessions import backend_session_scope
from backend.modules.base.query_builder import BaseQueryBuilder
from backend.modules.base.repositories import BaseRepo
from backend.modules.portfolio.entities import UniverseTop20


class UniverseTop20Repo(BaseRepo[Dict]):
    entity = UniverseTop20
    query_builder = BaseQueryBuilder(entity=entity)
    session_scope = backend_session_scope