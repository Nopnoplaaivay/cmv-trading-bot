from fastapi import Depends, Request
from starlette.responses import JSONResponse

from backend.common.consts import MessageConsts
from backend.common.responses import SuccessResponse
from backend.modules.auth.decorators import UserPayload
from backend.modules.auth.guards import auth_guard
from backend.modules.auth.types import JwtPayload
from backend.modules.portfolio.dtos import SetupDNSEAccountDTO
from backend.modules.portfolio.handlers import portfolio_router
from backend.modules.portfolio.services import AccountsService


@portfolio_router.post("/setup-account", dependencies=[Depends(auth_guard)])
async def setup_dnse_account(
    payload: SetupDNSEAccountDTO, user: JwtPayload = Depends(UserPayload)
):
    result = await AccountsService.setup_dnse_account(user=user, payload=payload)
    response = SuccessResponse(
        http_code=200,
        status_code=200,
        message=MessageConsts.SUCCESS,
        data=result,
    )
    return JSONResponse(status_code=response.http_code, content=response.to_dict())


# @accounts_router.post(
#     "/refresh-balance/{broker_account_id}", dependencies=[Depends(auth_guard)]
# )
# async def refresh_account_balance(
#     broker_account_id: str, user: JwtPayload = Depends(UserPayload)
# ):

#     result = await AccountsService.refresh_account_balance(
#         user=user, broker_account_id=broker_account_id
#     )
#     response = SuccessResponse(
#         http_code=200,
#         status_code=200,
#         message=MessageConsts.SUCCESS,
#         data=result.dict(),
#     )
#     return JSONResponse(status_code=response.http_code, content=response.to_dict())


# @accounts_router.get("/my-accounts", dependencies=[Depends(auth_guard)])
# async def get_my_accounts(user: JwtPayload = Depends(UserPayload)):
#     """
#     Get all accounts for the authenticated user with their balances.
#     Requires user authentication.
#     """
#     result = await AccountsService.get_user_accounts(user=user)
#     response = SuccessResponse(
#         http_code=200, status_code=200, message=MessageConsts.SUCCESS, data=result
#     )
#     return JSONResponse(status_code=response.http_code, content=response.to_dict())
