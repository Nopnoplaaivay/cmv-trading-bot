from typing import Dict, List, Optional

from backend.db.sessions import backend_session_scope
from backend.modules.base.query_builder import BaseQueryBuilder
from backend.modules.base.repositories import BaseRepo
from backend.modules.portfolio.entities import PersonalWeights


class PersonalWeightsRepo(BaseRepo[Dict]):
    entity = PersonalWeights
    query_builder = BaseQueryBuilder(entity=entity)
    session_scope = backend_session_scope