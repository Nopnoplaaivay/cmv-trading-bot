import datetime
import pytz

from backend.utils.time_utils import TimeUtils
from backend.modules.portfolio.services import PortfoliosService


# current_datetime = TimeUtils.get_current_vn_time()
# print(current_datetime)

# current_time = current_datetime.hour
# print(f"Current time in VN timezone: {current_time}")
# print(type(current_time))

# utcnow = datetime.datetime.now()
# print(utcnow)
# print(datetime.datetime.now(datetime.timezone.utc))

# print(pytz.timezone('Asia/Ho_Chi_Minh').utcoffset(utcnow))


from backend.modules.portfolio.services.data_providers.price_data_provider import (
    PriceDataProvider,
)


async def test_get_market_data():
    from_date = "2025-01-01"
    df = await PriceDataProvider.get_market_data()

    if df.empty:
        print("No data returned.")
    else:
        print(f"Data shape: {df.shape}")
        print(df.head())


async def test_update_portfolio_weights():
    user_id = 2
    portfolio_name = "Test Portfolio"
    symbols = ["VIC", "VHM", "MWG", "FPT", "VNM"]

    await PortfoliosService.create_custom_portfolio(
        user_id=user_id, portfolio_name=portfolio_name, symbols=symbols
    )
    print("Portfolio weights updated successfully.")


async def test_metadata_repo():
    from backend.modules.portfolio.repositories.portfolio_metadata import (
        PortfolioMetadataRepo,
    )

    conditions = {"portfolioId": "CUSTOM-3-PhuAnCut-78bcd64c"}
    records = await PortfolioMetadataRepo.get_by_condition(conditions=conditions)
    print(f"Records found: {records}")

    all_records = await PortfolioMetadataRepo.get_all()
    for record in all_records:
        print(record)


def test():
    unique_portfolio_ids = ["CUSTOM-3-PhuNgu-20b9a2cc", "CUSTOM-3-PhuOcCho-50fbf756"]
    portfolio_ids_string = "'" + "','".join(unique_portfolio_ids) + "'"
    print(portfolio_ids_string)


async def test_pnl_df():
    from backend.modules.portfolio.services import PortfoliosService

    portfolio_id = "CUSTOM-3-PhuOcCho-50fbf756"
    pnl_data = await PortfoliosService.get_portfolio_pnl(portfolio_id=portfolio_id)



if __name__ == "__main__":
    import asyncio

    # asyncio.run(test_update_portfolio_weights())
    # test()
    # asyncio.run(test_metadata_repo())
    asyncio.run(test_pnl_df())
