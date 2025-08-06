from fastapi import Depends, Request
from starlette.responses import JSONResponse

from backend.common.consts import MessageConsts
from backend.common.responses import SuccessResponse
from backend.modules.auth.decorators import UserPayload
from backend.modules.auth.guards import auth_guard
from backend.modules.auth.types import JwtPayload
from backend.modules.portfolio.dtos import SetupDNSEAccountDTO
from backend.modules.portfolio.handlers import accounts_router
from backend.modules.portfolio.services import AccountsService


@accounts_router.post("/setup", dependencies=[Depends(auth_guard)])
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
