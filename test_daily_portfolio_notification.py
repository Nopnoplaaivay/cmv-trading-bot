import asyncio

from backend.modules.portfolio.services import PortfolioNotificationService


if __name__ == "__main__":
    # For testing
    async def main():
        await PortfolioNotificationService.send_daily_portfolio_notification()

        # Or start the scheduler (uncomment to run continuously)
        # await service.run_scheduler()

    asyncio.run(main())
