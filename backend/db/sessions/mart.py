import os
from contextlib import contextmanager
from typing import ContextManager
import uuid

from sqlalchemy.orm import Session

from backend.db.connectors import CONTEXTVAR, SQLServerConnectorPool
from backend.utils.logger import LOGGER


PREFIX = "LOCAL_MART" if os.getenv("TEST") == "1" else "PROD_MART"
SESSIONS = {}
DNS = os.environ.get(f"{PREFIX}_DNS", None)
MIN_CONN = 5
MAX_CONN = 20

POOL = SQLServerConnectorPool(dns=DNS, max_conn=MAX_CONN, min_conn=MIN_CONN)


def set_session(session):
    global SESSIONS
    context_id = CONTEXTVAR.get()
    if session is None:
        del SESSIONS[context_id]
        return
    if context_id is None:
        context_id = uuid.uuid4()
    CONTEXTVAR.set(context_id)
    SESSIONS[context_id] = session


def get_session():
    global SESSIONS
    context_id = CONTEXTVAR.get()
    return SESSIONS.get(context_id, None)


@contextmanager
def mart_session_scope(new=False) -> ContextManager[Session]:
    """
    Provide a transactional scope around a series of operations.
    Shouldn't keep session alive too long, it will block a connection of pool connections.
    """
    if not new:
        session: Session
        reuse_session = get_session()
        if reuse_session is None:
            session = POOL.get()
            set_session(session=session)
        else:
            session = reuse_session
        try:
            yield session
            if reuse_session is None:
                session.commit()
        except Exception as exception:
            LOGGER.error(exception, exc_info=True)
            if reuse_session is None:
                session.rollback()
            raise exception
        finally:
            if reuse_session is None:
                POOL.put(session)
                set_session(session=None)
    else:
        session = POOL.get()
        try:
            yield session
            session.commit()
        except Exception as exception:
            LOGGER.error(exception, exc_info=True)
            session.rollback()
            raise exception
        finally:
            POOL.put(session)
