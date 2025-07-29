from .sql_server import SQLServerConnectorPool
import contextvars

CONTEXTVAR = contextvars.ContextVar("var", default=None)
