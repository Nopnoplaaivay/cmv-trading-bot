import asyncio
import time

from backend.modules.portfolio.services import UniverseTopMonthlyService, OptimizedWeightsService


if __name__ == "__main__":
    try:
        # asyncio.run(UniverseTopMonthlyService.update_newest_data_all_monthly())
        start_time = time.time()
        print("🔄 Updating Portfolio Weight Daily data...")
        asyncio.run(OptimizedWeightsService.update_newest_data_all_daily())
        end_time = time.time()
        print(f"✅ Universe Top Monthly data updated successfully in {end_time - start_time:.2f} seconds")
    except Exception as e:
        print(f"An error occurred: {e}")
    else:
        print("Data updated successfully.")