import asyncio
import schedule
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import pandas as pd

from backend.common.consts import SQLServerConsts
from backend.modules.portfolio.entities import OptimizedWeights
from backend.modules.portfolio.repositories import OptimizedWeightsRepo
from backend.modules.notifications.service import notification_service, notify_error
from backend.modules.notifications.telegram import MessageType
from backend.utils.time_utils import TimeUtils
from backend.utils.logger import LOGGER


LIMIT_WEIGHT_PCT = int(os.getenv("LIMIT_WEIGHT_PCT", 10))  # Maximum weight percentage for long positions


class DailyPortfolioNotificationService:
    repo = OptimizedWeightsRepo

    @classmethod
    def is_trading_day(cls, date: datetime) -> bool:
        return date.weekday() < 5

    @classmethod
    def get_last_trading_date(cls, current_date: datetime) -> datetime:
        check_date = current_date - timedelta(days=1)

        while not cls.is_trading_day(check_date):
            check_date -= timedelta(days=1)

        return check_date

    @classmethod
    async def get_portfolio_weights(cls, last_trading_date: str, current_date: str) -> Optional[Dict]:
        try:
            with cls.repo.session_scope() as session:
                conditions = {OptimizedWeights.date.name: last_trading_date}

                records = await cls.repo.get_by_condition(conditions=conditions)
                if len(records) == 0:
                    LOGGER.warning(f"No portfolio data found for date: {last_trading_date}")
                    return None

                long_only_positions = []
                market_neutral_positions = []

                for record in records:
                    symbol = record[OptimizedWeights.symbol.name]
                    initial_weight_pct = record[OptimizedWeights.initialWeight.name] * 100 or 0
                    neutralized_weight_pct = record[OptimizedWeights.neutralizedWeight.name] * 100 or 0

                    if initial_weight_pct > 1:
                        long_only_positions.append(
                            {
                                "symbol": symbol,
                                "weight": min(initial_weight_pct, LIMIT_WEIGHT_PCT)
                            }
                        )

                    if neutralized_weight_pct > 1: 
                        market_neutral_positions.append(
                            {
                                "symbol": symbol,
                                "weight": min(neutralized_weight_pct, LIMIT_WEIGHT_PCT)
                            }
                        )

                long_only_positions.sort(key=lambda x: x["weight"], reverse=True)
                market_neutral_positions.sort(key=lambda x: x["weight"], reverse=True)
                session.commit()


            return {
                "date": current_date,
                "long_only": long_only_positions,
                "market_neutral": market_neutral_positions,
            }

        except Exception as e:
            LOGGER.error(f"Error getting portfolio weights for {last_trading_date}: {e}")
            await notify_error(
                "PORTFOLIO DATA ERROR",
                f"Không thể lấy dữ liệu danh mục cho ngày {last_trading_date}: {str(e)}",
            )
            return None

    @classmethod
    async def send_daily_portfolio_notification(cls):
        try:
            current_date = TimeUtils.get_current_vn_time()

            # Check if today is a trading day
            if not cls.is_trading_day(current_date):
                LOGGER.info(f"Today ({current_date.strftime('%A %d/%m/%Y')}) is not a trading day. Skipping notification.")
                return

            # Get last trading date
            last_trading_date = cls.get_last_trading_date(current_date)
            last_trading_date_str = last_trading_date.strftime(SQLServerConsts.DATE_FORMAT)
            current_date_str = current_date.strftime(SQLServerConsts.DATE_FORMAT)

            LOGGER.info(f"Sending daily portfolio notification for {last_trading_date_str}")

            # Initialize notification service
            if not notification_service.is_ready():
                await notification_service.initialize()

            if not notification_service.is_ready():
                LOGGER.error("Notification service not available")
                return

            # Get portfolio data
            portfolio_data = await cls.get_portfolio_weights(last_trading_date_str, current_date_str)

            if not portfolio_data:
                await notify_error(
                    "KHÔNG CÓ DỮ LIỆU DANH MỤC",
                    f"Không tìm thấy dữ liệu danh mục cho ngày {last_trading_date.strftime('%d/%m/%Y')}",
                )
                return

            # Notify about daily portfolio weights
            await notification_service.notify_daily_portfolio(portfolio_data=portfolio_data)
            LOGGER.info("Daily portfolio notification sent successfully")

        except Exception as e:
            LOGGER.error(f"Error in daily portfolio notification: {e}")
            await notify_error(
                "LỖI THÔNG BÁO DANH MỤC",
                f"Có lỗi khi gửi thông báo danh mục hàng ngày: {str(e)}",
            )

    @classmethod
    def schedule_daily_notifications(cls):
        # notification_time = "07:00" if os.getenv("TEST") == "1" else "00:00"
        notification_time = "07:30" if os.getenv("TEST") == "1" else "00:00"
        schedule.every().day.at(notification_time).do(
            lambda: asyncio.create_task(cls.send_daily_portfolio_notification())
        )

        LOGGER.info(f"Daily portfolio notifications scheduled for {notification_time}")

    @classmethod
    async def run_scheduler(cls):
        cls.schedule_daily_notifications()

        LOGGER.info("Portfolio notification scheduler started")

        while True:
            schedule.run_pending()
            print(f"Scheduler running at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            await asyncio.sleep(60)  # Check every minute

    @classmethod
    async def send_test_notification(cls, date: Optional[str] = None):
        try:
            if date is None:
                # Use last trading date
                current_date = TimeUtils.get_current_vn_time()
                last_trading_date = cls.get_last_trading_date(current_date)
                date = last_trading_date.strftime("%Y-%m-%d")
                current_date_str = current_date.strftime(SQLServerConsts.DATE_FORMAT)

            LOGGER.info(f"Sending test portfolio notification for {date}")

            # Initialize notification service
            if not notification_service.is_ready():
                await notification_service.initialize()

            # Get and send portfolio data
            portfolio_data = await cls.get_portfolio_weights(last_trading_date=date, current_date=current_date_str)

            if portfolio_data:
                await notification_service.notify_daily_portfolio(portfolio_data=portfolio_data)
                print(f"✅ Test notification sent for {date}")
            else:
                print(f"❌ No portfolio data found for {date}")

        except Exception as e:
            print(f"❌ Error sending test notification: {e}")
            LOGGER.error(f"Error in test notification: {e}")


# Standalone function to run the scheduler
async def start_portfolio_notification_service():
    """
    Start the daily portfolio notification service.
    """
    service = DailyPortfolioNotificationService()
    await service.run_scheduler()
