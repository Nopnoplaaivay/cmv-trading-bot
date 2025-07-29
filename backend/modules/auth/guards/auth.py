from fastapi import Request
from typing import Optional

from backend.common.responses.exceptions import BaseExceptionResponse
from backend.common.consts import MessageConsts
from backend.modules.auth.services import AuthService


class AuthGuard:
    @classmethod
    async def activate(cls, request: Request):
        token = cls.extract_token_from_header(request)
        if not token:
            raise BaseExceptionResponse(
                http_code=401,
                status_code=401,
                message=MessageConsts.UNAUTHORIZED,
                errors="Missing or invalid token"
            )

        request.state.user = await AuthService.verify_access_token(access_token=token)
        return True

    def extract_token_from_header(request: Request) -> Optional[str]:
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return None
        
        parts = auth_header.split()
        if len(parts) == 2 and parts[0].lower() == "bearer":
            return parts[1]
        return None
    
async def auth_guard(request: Request):
    return await AuthGuard.activate(request)