import asyncio

from backend.modules.portfolio.services import UniverseTop20Service


if __name__ == "__main__":
    try:
        asyncio.run(UniverseTop20Service.update_newest_data_all_monthly())
    except Exception as e:
        print(f"An error occurred: {e}")
    else:
        print("Data updated successfully.")