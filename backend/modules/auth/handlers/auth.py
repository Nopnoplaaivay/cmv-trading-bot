from fastapi import Depends, Request
from starlette.responses import JSONResponse

from backend.common.consts import MessageConsts
from backend.common.responses.base import BaseResponse
from backend.common.responses import SuccessResponse
from backend.modules.auth.dtos import (
    RegisterDTO,
    LoginDTO,
    LogoutDTO,
    RefreshDTO
)
from backend.modules.auth.handlers import auth_router
from backend.modules.auth.services import AuthService
from backend.modules.auth.guards.roles import admin_guard


@auth_router.post("/register")
async def register(payload: RegisterDTO):
    await AuthService.register(payload=payload)
    response = SuccessResponse(
        http_code=201, status_code=201, message=MessageConsts.SUCCESS
    )
    return JSONResponse(status_code=response.http_code, content=response.to_dict())


@auth_router.post("/login")
async def login(payload: LoginDTO):
    token_pair = await AuthService.login(payload=payload)
    response = SuccessResponse(
        http_code=200, status_code=200, message=MessageConsts.SUCCESS, data=token_pair
    )
    return JSONResponse(status_code=response.http_code, content=response.to_dict())


@auth_router.post("/logout")
async def logout(payload: LogoutDTO):
    await AuthService.logout(payload=payload)
    return BaseResponse(http_code=200, status_code=200, message=MessageConsts.SUCCESS)


@auth_router.post("/refresh")
async def refresh_token(payload: RefreshDTO):
    token_pair = await AuthService.refresh_token(payload=payload)
    response = SuccessResponse(
        http_code=200, status_code=200, message=MessageConsts.SUCCESS, data=token_pair
    )
    return JSONResponse(status_code=response.http_code, content=response.to_dict())