from fastapi import Depends
from starlette.responses import JSONResponse

from backend.common.consts import MessageConsts
from backend.common.responses.base import BaseResponse
from backend.common.responses import SuccessResponse
from backend.modules.admin.handlers import admin_router
from backend.modules.admin.services import AdminService

from backend.modules.auth.decorators import UserPayload
from backend.modules.auth.guards import auth_guard, admin_guard
from backend.modules.auth.types import JwtPayload
from backend.modules.admin.dtos import UpdateRoleDTO, CreateUserDTO, UpdateUserInfoDTO


@admin_router.get("/get-users", dependencies=[Depends(auth_guard), Depends(admin_guard)])
async def get_users(user: JwtPayload = Depends(UserPayload)):
    users = await AdminService.get_all_users()
    response = SuccessResponse(
        http_code=200,
        status_code=200,
        message=MessageConsts.SUCCESS,
        data=users,
    )
    return JSONResponse(status_code=response.http_code, content=response.to_dict())


@admin_router.post("/create-user", dependencies=[Depends(auth_guard), Depends(admin_guard)])
async def create_user(payload: CreateUserDTO, user: JwtPayload = Depends(UserPayload)):
    new_user = await AdminService.create_user(admin_user=user, payload=payload)
    response = SuccessResponse(
        http_code=201,
        status_code=201,
        message=MessageConsts.SUCCESS,
        data=new_user,
    )
    return JSONResponse(status_code=response.http_code, content=response.to_dict())


@admin_router.put("/update-user", dependencies=[Depends(auth_guard), Depends(admin_guard)])
async def update_user(payload: UpdateUserInfoDTO, user: JwtPayload = Depends(UserPayload)):
    updated_user = await AdminService.update_user_info(admin_user=user, payload=payload)
    response = SuccessResponse(
        http_code=200,
        status_code=200,
        message=MessageConsts.SUCCESS,
        data=updated_user,
    )
    return JSONResponse(status_code=response.http_code, content=response.to_dict())


@admin_router.delete("/delete-user/{user_id}", dependencies=[Depends(auth_guard), Depends(admin_guard)])
async def delete_user(user_id: str, user: JwtPayload = Depends(UserPayload)):
    await AdminService.delete_user(admin_user=user, user_id=user_id)
    return None


@admin_router.get("/get-user-details/{user_id}", dependencies=[Depends(auth_guard), Depends(admin_guard)])
async def get_user_details(user_id: str, user: JwtPayload = Depends(UserPayload)):
    user_details = await AdminService.get_user_details(admin_user=user, user_id=user_id)
    response = SuccessResponse(
        http_code=200,
        status_code=200,
        message=MessageConsts.SUCCESS,
        data=user_details,
    )
    return JSONResponse(status_code=response.http_code, content=response.to_dict())