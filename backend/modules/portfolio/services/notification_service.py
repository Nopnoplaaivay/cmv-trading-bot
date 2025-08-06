from typing import Optional

from backend.common.consts import SQLServerConsts
from backend.modules.auth.types import JwtPayload
from backend.modules.portfolio.services.data_providers import PortfolioDataProvider
from backend.modules.portfolio.services.analysis_service import PortfolioAnalysisService
from backend.modules.portfolio.infrastructure import (
    TradingCalendarService,
    PortfolioReportGenerator,
)
from backend.modules.notifications.service import notification_service
from backend.modules.notifications.service import notify_error
from backend.modules.notifications.telegram import MessageType
from backend.utils.time_utils import TimeUtils
from backend.utils.logger import LOGGER


class PortfolioNotificationService:
    portfolio_data_provider = PortfolioDataProvider
    trading_calendar = TradingCalendarService

    @classmethod
    async def send_daily_portfolio_notification(cls):
        try:
            last_trading_date, next_trading_date = cls.trading_calendar.get_last_next_trading_dates()
            if not last_trading_date or not next_trading_date:
                LOGGER.warning(
                    "No trading dates found. Cannot proceed with portfolio analysis."
                )
                return False
            next_trading_date_str = next_trading_date.strftime(SQLServerConsts.DATE_FORMAT)
            last_trading_date_str = last_trading_date.strftime(SQLServerConsts.DATE_FORMAT)

            LOGGER.info(f"Sending daily portfolio notification for {next_trading_date_str}")

            # Initialize notification service
            if not notification_service.is_ready():
                await notification_service.initialize()

            if not notification_service.is_ready():
                LOGGER.error("Notification service not available")
                return False

            # Get portfolio data
            portfolio_data = await cls.portfolio_data_provider.get_portfolio_weights(
                last_trading_date_str, next_trading_date_str
            )

            if not portfolio_data:
                return True

            # Notify about daily portfolio weights
            await notification_service.notify_daily_portfolio(
                portfolio_data=portfolio_data
            )
            LOGGER.info("Daily portfolio notification sent successfully")
            return True

        except Exception as e:
            LOGGER.error(f"Error in daily portfolio notification: {e}")
            await notify_error(
                "LỖI THÔNG BÁO DANH MỤC",
                f"Có lỗi khi gửi thông báo danh mục hàng ngày: {str(e)}",
            )
            return False

    @classmethod
    async def send_test_notification(cls, date: Optional[str] = None):
        try:
            current_date = TimeUtils.get_current_vn_time()

            if not cls.trading_calendar.is_trading_day(current_date):
                LOGGER.info(f"Today ({current_date.strftime('%A %d/%m/%Y')}) is not a trading day. Skipping notification.")
                return
            
            current_hour = current_date.hour
            if current_hour >= 18:
                last_trading_date = current_date
            else:
                last_trading_date = cls.trading_calendar.get_last_trading_date(current_date)
            
            next_trading_date = cls.trading_calendar.get_next_trading_date(current_date)
            next_trading_date_str = next_trading_date.strftime(SQLServerConsts.DATE_FORMAT)
            last_trading_date_str = last_trading_date.strftime(SQLServerConsts.DATE_FORMAT)

            LOGGER.info(f"Sending test portfolio notification for {date}")

            # Initialize notification service
            if not notification_service.is_ready():
                await notification_service.initialize()

            # Get and send portfolio data
            portfolio_data = await cls.portfolio_data_provider.get_portfolio_weights(
                last_trading_date=last_trading_date_str, next_trading_date=next_trading_date_str
            )

            if portfolio_data:
                await notification_service.notify_daily_portfolio(
                    portfolio_data=portfolio_data
                )
                print(f"✅ Test notification sent for {next_trading_date_str}")
            else:
                print(f"❌ No portfolio data found for {next_trading_date_str}")

        except Exception as e:
            print(f"❌ Error sending test notification: {e}")
            LOGGER.error(f"Error in test notification: {e}")

    @classmethod
    async def send_portfolio_analysis_report(
        cls,
        broker_account_id: str,
        strategy_type: str = "market_neutral",
        include_trade_plan: bool = True,
        message_type: MessageType = MessageType.INFO,
    ):
        try:
            LOGGER.info(
                f"Generating portfolio analysis report for account {broker_account_id}"
            )

            # Initialize notification service
            if not notification_service.is_ready():
                await notification_service.initialize()

            if not notification_service.is_ready():
                LOGGER.error("Notification service not available")
                await notify_error(
                    "TELEGRAM SERVICE ERROR",
                    "Telegram service không khả dụng để gửi báo cáo portfolio",
                )
                return False

            # Generate portfolio analysis
            analysis_result = await PortfolioAnalysisService.analyze_portfolio(
                broker_account_id=broker_account_id, strategy_type=strategy_type
            )

            if not analysis_result:
                error_msg = f"Không thể phân tích portfolio cho tài khoản {broker_account_id}"
                LOGGER.warning(error_msg)
                await notify_error("PORTFOLIO ANALYSIS ERROR", error_msg)
                return False

            # Convert analysis result back to objects for report generation
            current_positions = []
            recommendations = []

            # Note: We'd need to convert dict back to objects here if needed
            # For now, let's generate report directly from the analysis data

            # Generate text report
            report_text = PortfolioReportGenerator.generate_telegram_report(
                analysis_result=analysis_result, include_trade_plan=include_trade_plan
            )

            # Send report via Telegram
            success = await notification_service.telegram.send_message(
                text=report_text,
                message_type=message_type,
                parse_mode="HTML",
                disable_notification=False,
            )

            if success:
                LOGGER.info(
                    f"Portfolio analysis report sent successfully for account {broker_account_id}"
                )
                return True
            else:
                LOGGER.error(
                    f"Failed to send portfolio analysis report for account {broker_account_id}"
                )
                return False

        except Exception as e:
            LOGGER.error(f"Error sending portfolio analysis report: {e}")
            await notify_error(
                "PORTFOLIO REPORT ERROR",
                f"Lỗi khi gửi báo cáo phân tích portfolio: {str(e)}",
            )
            return False
