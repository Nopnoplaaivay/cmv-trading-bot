from typing import Optional
from fastapi import Request

from backend.common.responses.exceptions import BaseExceptionResponse
from backend.modules.auth.services import AuthService


class RoleGuard:
    @classmethod
    async def activate(cls, request: Request, required_role: str = None):
        if not required_role:
            return True

        token = cls.extract_token_from_header(request)
        if not token:
            raise BaseExceptionResponse(
                http_code=401,
                status_code=401,
                message="Unauthorized",
                errors="Missing or invalid token"
            )

        request.state.user = await AuthService.verify_access_token(access_token=token)
        user = request.state.user
        if not user:
            raise BaseExceptionResponse(
                http_code=401,
                status_code=401,
                message="Unauthorized",
                errors="Missing or invalid token"
            )
        if user.role != required_role:
            raise BaseExceptionResponse(
                http_code=403,
                status_code=403,
                message="Forbidden",
                errors=f"User does not have the required role: {required_role}"
            )
        return True

    def extract_token_from_header(request: Request) -> Optional[str]:
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return None

        parts = auth_header.split()
        if len(parts) == 2 and parts[0].lower() == "bearer":
            return parts[1]
        return None

    
async def admin_guard(request: Request):
    return await RoleGuard.activate(request, required_role="admin")