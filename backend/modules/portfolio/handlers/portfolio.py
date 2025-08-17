from typing import List
from fastapi import Depends, Query
from httpcore import request
from starlette.responses import JSONResponse

from backend.common.consts import MessageConsts
from backend.common.responses.base import BaseResponse
from backend.common.responses import SuccessResponse
from backend.modules.portfolio.handlers import portfolio_router
from backend.modules.portfolio.services import (
    PortfolioAnalysisService,
    PortfolioNotificationService,
    PortfoliosService,
)
from backend.modules.portfolio.dtos import (
    CreateCustomPortfolioDTO,
    UpdatePortfolioDTO,
    AnalyzePortfolioDTO,
)
from backend.modules.auth.decorators import UserPayload
from backend.modules.auth.guards import auth_guard, premium_guard
from backend.modules.auth.types import JwtPayload
from backend.modules.notifications.telegram import MessageType


@portfolio_router.get("/me", dependencies=[Depends(auth_guard)])
async def get_my_portfolios(user: JwtPayload = Depends(UserPayload)):
    portfolios = await PortfoliosService.get_portfolios_by_user_id(user=user)
    response = SuccessResponse(
        http_code=200, status_code=200, message=MessageConsts.SUCCESS, data=portfolios
    )

    return JSONResponse(status_code=response.http_code, content=response.to_dict())


@portfolio_router.get("/system", dependencies=[Depends(auth_guard)])
async def get_system_portfolios(user: JwtPayload = Depends(UserPayload)):
    portfolios = await PortfoliosService.get_system_portfolios()
    response = SuccessResponse(
        http_code=200, status_code=200, message=MessageConsts.SUCCESS, data=portfolios
    )

    return JSONResponse(status_code=response.http_code, content=response.to_dict())


@portfolio_router.get("/symbols", dependencies=[Depends(auth_guard)])
async def get_available_symbols(user: JwtPayload = Depends(UserPayload)):
    available_symbols = await PortfoliosService.get_available_symbols()
    response = SuccessResponse(
        http_code=200,
        status_code=200,
        message=MessageConsts.SUCCESS,
        data=available_symbols,
    )
    return JSONResponse(status_code=response.http_code, content=response.to_dict())


@portfolio_router.get("/pnl/{portfolio_id}", dependencies=[Depends(auth_guard)])
async def get_portfolio_pnl_by_id(
    portfolio_id: str,
    strategy: str = "LongOnly",
    user: JwtPayload = Depends(UserPayload),
):
    pnl = await PortfoliosService.get_portfolio_pnl(
        portfolio_id=portfolio_id, strategy=strategy
    )
    response = SuccessResponse(
        http_code=200, status_code=200, message=MessageConsts.SUCCESS, data=pnl
    )

    return JSONResponse(status_code=response.http_code, content=response.to_dict())


@portfolio_router.get("/{portfolio_id}", dependencies=[Depends(auth_guard)])
async def get_portfolios_by_id(
    portfolio_id: str, user: JwtPayload = Depends(UserPayload)
):
    portfolio = await PortfoliosService.get_portfolios_by_id(
        portfolio_id=portfolio_id, user=user
    )
    response = SuccessResponse(
        http_code=200, status_code=200, message=MessageConsts.SUCCESS, data=portfolio
    )

    return JSONResponse(status_code=response.http_code, content=response.to_dict())


@portfolio_router.post("/create", dependencies=[Depends(premium_guard)])
async def create_custom_portfolio(
    payload: CreateCustomPortfolioDTO, user: JwtPayload = Depends(UserPayload)
):
    create_result = await PortfoliosService.create_portfolio(
        user_id=user.userId,
        portfolio_name=payload.portfolio_name,
        portfolio_desc=payload.portfolio_desc,
        symbols=payload.symbols,
    )

    response = SuccessResponse(
        http_code=201,
        status_code=201,
        message=MessageConsts.CREATED,
        data=create_result,
    )

    return JSONResponse(status_code=response.http_code, content=response.to_dict())


@portfolio_router.put("/update", dependencies=[Depends(premium_guard)])
async def update_portfolio(
    payload: UpdatePortfolioDTO, user: JwtPayload = Depends(UserPayload)
):
    if not payload.symbols or len(payload.symbols) < 2:
        response = BaseResponse(
            http_code=400,
            status_code=400,
            message=MessageConsts.BAD_REQUEST,
            errors="Portfolio must contain at least 2 symbols",
        )
        return JSONResponse(status_code=response.http_code, content=response.to_dict())

    # Update portfolio symbols
    update_result = await PortfoliosService.update_portfolio(
        portfolio_id=payload.portfolio_id, symbols=payload.symbols, user=user
    )

    response = SuccessResponse(
        http_code=200,
        status_code=200,
        message=MessageConsts.SUCCESS,
        data=update_result,
    )

    return JSONResponse(status_code=response.http_code, content=response.to_dict())


@portfolio_router.delete("/{portfolio_id}", dependencies=[Depends(premium_guard)])
async def delete_portfolio(portfolio_id: str, user: JwtPayload = Depends(UserPayload)):
    delete_result = await PortfoliosService.delete_portfolio(portfolio_id=portfolio_id)

    response = SuccessResponse(
        http_code=200,
        status_code=200,
        message=MessageConsts.SUCCESS,
        data=delete_result,
    )

    return JSONResponse(status_code=response.http_code, content=response.to_dict())


@portfolio_router.post(
    "/analysis/{broker_account_id}", dependencies=[Depends(auth_guard)]
)
async def get_portfolio_analysis(
    broker_account_id: str,
    payload: AnalyzePortfolioDTO,
    user: JwtPayload = Depends(UserPayload),
):
    analysis_result = await PortfolioAnalysisService.analyze_portfolio(
        broker_account_id=broker_account_id,
        portfolio_id=payload.portfolio_id,
        strategy_type=payload.strategy_type,
    )
    response = SuccessResponse(
        http_code=200,
        status_code=200,
        message=MessageConsts.SUCCESS,
        data=analysis_result,
    )
    return JSONResponse(status_code=response.http_code, content=response.to_dict())


@portfolio_router.post(
    "/notify/{broker_account_id}", dependencies=[Depends(auth_guard)]
)
async def send_portfolio_report_notification(
    broker_account_id: str,
    user: JwtPayload = Depends(UserPayload),
    strategy_type: str = Query(
        default="MarketNeutral", description="Portfolio strategy type"
    ),
    include_trade_plan: bool = Query(
        default=True, description="Include trade recommendations in report"
    ),
):
    notify_result = await PortfolioNotificationService.send_portfolio_analysis_report(
        broker_account_id=broker_account_id,
        strategy_type=strategy_type,
        include_trade_plan=include_trade_plan,
        message_type=MessageType.CHART,
    )

    response = SuccessResponse(
        http_code=200,
        status_code=200,
        message="Portfolio report sent to Telegram successfully",
        data=notify_result,
    )

    return JSONResponse(status_code=response.http_code, content=response.to_dict())
