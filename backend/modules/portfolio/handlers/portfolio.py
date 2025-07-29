from fastapi import Depends
from starlette.responses import JSONResponse

from backend.common.consts import MessageConsts
from backend.common.responses.base import BaseResponse
from backend.common.responses import SuccessResponse
from backend.modules.portfolio.handlers import portfolio_router
# from backend.modules.investors.services import AccountsService, HoldingsService
# from backend.modules.auth.decorators import UserPayload
# from backend.modules.auth.guards import auth_guard
# from backend.modules.auth.types import JwtPayload
# from backend.modules.investors.dtos import DepositDTO, WithdrawDTO


# @portfolio_router.get("/balance", dependencies=[Depends(auth_guard)])
# async def get_balance(payload: JwtPayload = Depends(UserPayload)):
#     account_balance = await AccountsService.get_balance(payload=payload)
#     if not account_balance:
#         response = BaseResponse(
#             http_code=404,
#             status_code=404,
#             message=MessageConsts.NOT_FOUND,
#             errors="Account balance not found",
#         )
#         return JSONResponse(status_code=response.http_code, content=response.to_dict())
#     response = SuccessResponse(
#         http_code=200,
#         status_code=200,
#         message=MessageConsts.SUCCESS,
#         data=account_balance,
#     )
#     return JSONResponse(status_code=response.http_code, content=response.to_dict())

