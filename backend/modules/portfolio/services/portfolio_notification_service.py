from backend.common.consts import SQLServerConsts, MessageConsts
from backend.common.responses.exceptions import BaseExceptionResponse
from backend.modules.portfolio.services.data_providers import PortfolioDataProvider
from backend.modules.portfolio.services.portfolio_analysis_service import PortfolioAnalysisService
from backend.modules.portfolio.infrastructure import (
    TradingCalendarService,
    PortfolioReportGenerator
)
from backend.modules.notifications.service import notification_service
from backend.modules.notifications.service import notify_error
from backend.modules.notifications.telegram import MessageType
from backend.utils.logger import LOGGER


class PortfolioNotificationService:
    portfolio_data_provider = PortfolioDataProvider
    trading_calendar = TradingCalendarService

    @classmethod
    async def send_daily_system_portfolio(cls):
        try:
            last_trading_date, next_trading_date = (
                cls.trading_calendar.get_last_next_trading_dates()
            )
            if not last_trading_date or not next_trading_date:
                LOGGER.warning("No trading dates found. Cannot proceed with portfolio analysis.")
                raise BaseExceptionResponse(
                    http_code=400,
                    status_code=400,
                    message=MessageConsts.NOT_FOUND,
                    errors=None
                )
            
            next_trading_date_str = next_trading_date.strftime(SQLServerConsts.DATE_FORMAT)
            last_trading_date_str = last_trading_date.strftime(SQLServerConsts.DATE_FORMAT)

            # Initialize notification service
            if not notification_service.is_ready():
                await notification_service.initialize()

            if not notification_service.is_ready():
                LOGGER.error("Notification service not available")
                raise BaseExceptionResponse(
                    http_code=400,
                    status_code=400,
                    message=MessageConsts.NOT_FOUND,
                    errors=None
                )

            # Get portfolio data
            portfolio_data = await cls.portfolio_data_provider.get_system_portfolio(
                last_trading_date_str, next_trading_date_str
            )

            if not portfolio_data:
                raise BaseExceptionResponse(
                    http_code=404,
                    status_code=404,
                    message=MessageConsts.NOT_FOUND,
                    errors=None
                )

            # Notify about daily portfolio weights
            await notification_service.notify_daily_portfolio(portfolio_data=portfolio_data)
            return {"message": "Daily portfolio notification sent successfully"}

        except Exception as e:
            raise BaseExceptionResponse(
                http_code=500,
                status_code=500,
                message=MessageConsts.INTERNAL_SERVER_ERROR,
                errors=str(e)
            )

    @classmethod
    async def send_portfolio_analysis_report(
        cls,
        broker_account_id: str,
        strategy_type: str = "market_neutral",
        include_trade_plan: bool = True,
        message_type: MessageType = MessageType.INFO,
    ):
        try:
            LOGGER.info(f"Generating portfolio analysis report for account {broker_account_id}")

            # Generate portfolio analysis
            analysis_result = await PortfolioAnalysisService.analyze_system_portfolio(
                broker_account_id=broker_account_id, strategy_type=strategy_type
            )

            if not analysis_result:
                error_msg = (
                    f"Không thể phân tích portfolio cho tài khoản {broker_account_id}"
                )
                LOGGER.warning(error_msg)
                await notify_error("PORTFOLIO ANALYSIS ERROR", error_msg)
                return False

            # Generate text report
            report_text = PortfolioReportGenerator.generate_telegram_report(
                analysis_result=analysis_result, include_trade_plan=include_trade_plan
            )

            if not notification_service.is_ready():
                await notification_service.initialize()

            if not notification_service.is_ready():
                return False

            # Send report via Telegram
            success = await notification_service.telegram.send_message(
                text=report_text,
                message_type=message_type,
                parse_mode="HTML",
                disable_notification=False,
            )

            if success:
                LOGGER.info(f"Portfolio analysis report sent successfully for account {broker_account_id}")
                return {"message": "Portfolio analysis report sent successfully"}
            else:
                LOGGER.error(f"Failed to send portfolio analysis report for account {broker_account_id}")
                return {"message": "Failed to send portfolio analysis report"}

        except Exception as e:
            LOGGER.error(f"Error sending portfolio analysis report for account {broker_account_id}: {e}")
            raise BaseExceptionResponse(
                http_code=500,
                status_code=500,
                message=MessageConsts.INTERNAL_SERVER_ERROR,
                errors=str(e)
            )
