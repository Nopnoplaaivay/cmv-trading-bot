from datetime import datetime
import asyncio
import os
import schedule

from backend.modules.portfolio.services import PortfolioNotificationService
from backend.utils.logger import LOGGER

# Scheduler Service
class PortfolioSchedulerService:

    def schedule_daily_notifications(self):
        """Schedule daily notifications"""
        notification_time = "07:30" if os.getenv("TEST") == "1" else "00:00"
        schedule.every().day.at(notification_time).do(
            lambda: asyncio.create_task(
                PortfolioNotificationService.send_daily_portfolio_notification()
            )
        )
        LOGGER.info(f"Daily portfolio notifications scheduled for {notification_time}")

    async def run_scheduler(self):
        """Run the notification scheduler"""
        self.schedule_daily_notifications()
        LOGGER.info("Portfolio notification scheduler started")

        while True:
            schedule.run_pending()
            print(
                f"Scheduler running at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )
            await asyncio.sleep(60)  # Check every minute