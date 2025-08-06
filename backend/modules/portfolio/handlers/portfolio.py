from fastapi import Depends, Query
from starlette.responses import JSONResponse

from backend.common.consts import MessageConsts
from backend.common.responses.base import BaseResponse
from backend.common.responses import SuccessResponse
from backend.modules.portfolio.handlers import portfolio_router
from backend.modules.portfolio.services import (
    PortfolioAnalysisService,
    PortfolioNotificationService,
)
from backend.modules.auth.decorators import UserPayload
from backend.modules.auth.guards import auth_guard
from backend.modules.auth.types import JwtPayload
from backend.modules.notifications.telegram import MessageType


@portfolio_router.get(
    "/analysis/{broker_account_id}", dependencies=[Depends(auth_guard)]
)
async def get_analysis(broker_account_id: str, user: JwtPayload = Depends(UserPayload)):
    analysis_result = await PortfolioAnalysisService.analyze_portfolio(
        broker_account_id=broker_account_id
    )
    if not analysis_result:
        response = BaseResponse(
            http_code=404,
            status_code=404,
            message=MessageConsts.NOT_FOUND,
            errors="Portfolio analysis failed",
        )
        return JSONResponse(status_code=response.http_code, content=response.to_dict())
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
        default="market_neutral", description="Portfolio strategy type"
    ),
    include_trade_plan: bool = Query(
        default=True, description="Include trade recommendations in report"
    ),
):
    """Send portfolio analysis report to Telegram"""
    try:
        success = await PortfolioNotificationService.send_portfolio_analysis_report(
            broker_account_id=broker_account_id,
            strategy_type=strategy_type,
            include_trade_plan=include_trade_plan,
            message_type=MessageType.CHART,
        )

        if success:
            response = SuccessResponse(
                http_code=200,
                status_code=200,
                message="Portfolio report sent to Telegram successfully",
                data={
                    "account_id": broker_account_id,
                    "strategy_type": strategy_type,
                    "notification_sent": True,
                    "include_trade_plan": include_trade_plan,
                },
            )
        else:
            response = BaseResponse(
                http_code=500,
                status_code=500,
                message="Failed to send portfolio report to Telegram",
                errors="Notification service error",
            )

        return JSONResponse(status_code=response.http_code, content=response.to_dict())

    except Exception as e:
        response = BaseResponse(
            http_code=500,
            status_code=500,
            message=MessageConsts.INTERNAL_SERVER_ERROR,
            errors=f"Error sending notification: {str(e)}",
        )
        return JSONResponse(status_code=response.http_code, content=response.to_dict())