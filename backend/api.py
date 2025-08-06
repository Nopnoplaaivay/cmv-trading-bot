from typing import List

from fastapi import APIRouter
from starlette.responses import JSONResponse

from backend.common.consts import MessageConsts
from backend.modules.base.dto import BaseDTO
from backend.modules.auth.handlers import auth_router
from backend.modules.admin.handlers import admin_router
from backend.modules.portfolio.handlers import portfolio_router, accounts_router
# from backend.modules.investors.handlers import investors_router
# from backend.modules.orders.handlers import orders_router


class ErrorDetailModel(BaseDTO):
    field: List[str]


class ErrorResponseModel(BaseDTO):
    statusCode: int
    message: str
    error: ErrorDetailModel


api_router = APIRouter(
    default_response_class=JSONResponse,
    responses={
        400: {"model": ErrorResponseModel},
        401: {"model": ErrorResponseModel},
        422: {"model": ErrorResponseModel},
        500: {"model": ErrorResponseModel},
    },
)


# api_router.include_router(investors_router, prefix="/investors-service", tags=["investors"])
# api_router.include_router(orders_router, prefix="/orders-service", tags=["orders"])
api_router.include_router(admin_router, prefix="/admin-service", tags=["admin"])
api_router.include_router(auth_router, prefix="/auth-service", tags=["auth"])
api_router.include_router(portfolio_router, prefix="/portfolio-service", tags=["portfolio"])
api_router.include_router(accounts_router, prefix="/accounts-service", tags=["accounts"])


@api_router.get("/healthcheck", include_in_schema=False)
def healthcheck():
    return JSONResponse(status_code=200, content={"message": MessageConsts.SUCCESS})