from fastapi import Depends
from starlette.responses import JSONResponse

from backend.common.consts import MessageConsts
from backend.common.responses.base import BaseResponse
from backend.common.responses import SuccessResponse
from backend.modules.admin.handlers import admin_router
from backend.modules.admin.services import AdminService
from backend.modules.portfolio.services import (
    BalanceService, 
    DealsService,
    DailyDataPipelineService,
    PortfolioNotificationService
)
from backend.modules.auth.decorators import UserPayload
from backend.modules.auth.guards import admin_guard
from backend.modules.auth.types import JwtPayload
from backend.modules.admin.dtos import UpdateRoleDTO



@admin_router.get("/update-balances", dependencies=[Depends(admin_guard)])
async def update_balances(user: JwtPayload = Depends(UserPayload)):
    success = await BalanceService.update_newest_balances_daily()
    response = SuccessResponse(
        http_code=200,
        status_code=200,
        message=MessageConsts.SUCCESS,
        data=success,
    )
    return JSONResponse(status_code=response.http_code, content=response.to_dict())


@admin_router.get("/update-deals", dependencies=[Depends(admin_guard)])
async def update_deals(user: JwtPayload = Depends(UserPayload)):
    success = await DealsService.update_newest_deals_daily()
    response = SuccessResponse(
        http_code=200,
        status_code=200,
        message=MessageConsts.SUCCESS,
        data=success,
    )
    return JSONResponse(status_code=response.http_code, content=response.to_dict())


@admin_router.post("/update-role", dependencies=[Depends(admin_guard)])
async def update_user_role(payload: UpdateRoleDTO, user: JwtPayload = Depends(UserPayload)):
    updated_user = await AdminService.update_user_role(admin_user=user, payload=payload)
    response = SuccessResponse(
        http_code=200,
        status_code=200,
        message=MessageConsts.SUCCESS,
        data=updated_user,
    )
    return JSONResponse(status_code=response.http_code, content=response.to_dict())


@admin_router.get("/send-system-notification", dependencies=[Depends(admin_guard)])
async def send_system_notification(user: JwtPayload = Depends(UserPayload)):
    try:
        notification_results = await PortfolioNotificationService.send_daily_system_portfolio()
        response = SuccessResponse(
            http_code=200,
            status_code=200,
            message=MessageConsts.SUCCESS,
            data=notification_results,
        )
        return JSONResponse(status_code=response.http_code, content=response.to_dict())
    except Exception as e:
        response = BaseResponse(
            http_code=500,
            status_code=500,
            message=str(e),
            errors=None
        )
        return JSONResponse(status_code=response.http_code, content=response.to_dict())


@admin_router.get("/run-pipeline", dependencies=[Depends(admin_guard)])
async def run_daily_pipeline(user: JwtPayload = Depends(UserPayload)):
    try:
        pipeline_results = await DailyDataPipelineService.run_manual()
        response = SuccessResponse(
            http_code=200,
            status_code=200,
            message=MessageConsts.SUCCESS,
            data=pipeline_results,
        )
        return JSONResponse(status_code=response.http_code, content=response.to_dict())
    except Exception as e:
        response = BaseResponse(
            http_code=500,
            status_code=500,
            message=str(e),
            errors=None
        )
        return JSONResponse(status_code=response.http_code, content=response.to_dict())