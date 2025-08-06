"""
Daily Data Pipeline Service

This service runs the daily data update pipeline automatically at 7PM every day.
It can be run as a standalone background service.

The pipeline will:
1. Update balance data for all accounts
2. Update deals data for all accounts
3. Update universe top monthly data
4. Update optimized weights
5. Send portfolio notifications to all users

The service will run continuously and execute the pipeline at 7PM Vietnam time each day.
"""

import asyncio
import sys
from pathlib import Path

from backend.modules.portfolio.services.daily_pipeline_service import DailyDataPipelineService
from backend.utils.logger import LOGGER


async def main():
    """Main entry point for the daily data pipeline service"""
    try:
        LOGGER.info("Starting Daily Data Pipeline Service...")
        LOGGER.info("Pipeline will run automatically at 7:00 PM Vietnam time daily")

        # Start the scheduler
        await DailyDataPipelineService.schedule_daily_run()

    except KeyboardInterrupt:
        LOGGER.info("Daily Data Pipeline Service stopped by user")
    except Exception as e:
        LOGGER.error(f"Fatal error in Daily Data Pipeline Service: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
