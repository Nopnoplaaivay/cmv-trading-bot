import asyncio

from backend.modules.portfolio.services import DailyPortfolioNotificationService


if __name__ == "__main__":
    # For testing
    async def main():
        service = DailyPortfolioNotificationService()

        # Send test notification
        await service.send_test_notification()

        # Or start the scheduler (uncomment to run continuously)
        # await service.run_scheduler()

    asyncio.run(main())
