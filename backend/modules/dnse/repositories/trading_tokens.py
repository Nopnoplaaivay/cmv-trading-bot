from typing import Dict

from backend.db.sessions import backend_session_scope
from backend.modules.base.query_builder import BaseQueryBuilder
from backend.modules.base.repositories import BaseRepo
from backend.modules.dnse.entities import TradingTokens


class TradingTokensRepo(BaseRepo[Dict]):
    entity = TradingTokens
    query_builder = BaseQueryBuilder(entity=entity)
    session_scope = backend_session_scope