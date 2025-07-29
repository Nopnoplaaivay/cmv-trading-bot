from fastapi import Request

from backend.modules.auth.types.auth import JwtPayload
from backend.common.responses.exceptions import BaseExceptionResponse


def UserPayload(request: Request) -> JwtPayload:
    user = getattr(request.state, "user", None)
    if not user:
        raise BaseExceptionResponse(
            http_code=401,
            status_code=401,
            message="Unauthorized",
            errors="User not authenticated"
        )
    return user