import asyncio

from backend.modules.portfolio.services.portfolio_daily_pipeline_service import DailyDataPipelineService
from backend.utils.logger import LOGGER


async def main():
    try:
        LOGGER.info("Starting Daily Data Pipeline Service...")
        LOGGER.info("Pipeline will run automatically at 7:00 PM Vietnam time daily")

        # Start the scheduler
        await DailyDataPipelineService.run_manual()

    except KeyboardInterrupt:
        LOGGER.info("Daily Data Pipeline Service stopped by user")
    except Exception as e:
        LOGGER.error(f"Fatal error in Daily Data Pipeline Service: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
