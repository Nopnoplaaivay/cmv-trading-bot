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
from backend.modules.admin.dtos import UpdateRoleDTO


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

@admin_router.post("/update-role", dependencies=[Depends(auth_guard), Depends(admin_guard)])
async def update_user_role(payload: UpdateRoleDTO, user: JwtPayload = Depends(UserPayload)):
    updated_user = await AdminService.update_user_role(admin_user=user, payload=payload)
    response = SuccessResponse(
        http_code=200,
        status_code=200,
        message=MessageConsts.SUCCESS,
        data=updated_user,
    )
    return JSONResponse(status_code=response.http_code, content=response.to_dict())
