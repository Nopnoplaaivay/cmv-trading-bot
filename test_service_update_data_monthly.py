import asyncio

from backend.modules.portfolio.services import UniverseTopMonthlyService, OptimizedWeightsService


if __name__ == "__main__":
    try:
        asyncio.run(UniverseTopMonthlyService.update_newest_data_all_monthly())
        asyncio.run(OptimizedWeightsService.update_newest_data_all_daily())
    except Exception as e:
        print(f"An error occurred: {e}")
    else:
        print("Data updated successfully.")