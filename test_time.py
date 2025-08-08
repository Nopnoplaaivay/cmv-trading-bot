import datetime
import pytz

from backend.utils.time_utils import TimeUtils


current_datetime = TimeUtils.get_current_vn_time()
print(current_datetime)

current_time = current_datetime.hour
print(f"Current time in VN timezone: {current_time}")
print(type(current_time))

utcnow = datetime.datetime.now()
print(utcnow)
print(datetime.datetime.now(datetime.timezone.utc))

print(pytz.timezone('Asia/Ho_Chi_Minh').utcoffset(utcnow))


from backend.modules.portfolio.services.data_providers.price_data_provider import PriceDataProvider


async def test_get_price_data_pivoted():
    from_date = "2025-01-01"
    df = await PriceDataProvider.get_price_data_pivoted()
    
    if df.empty:
        print("No data returned.")
    else:
        print(f"Data shape: {df.shape}")
        print(df.head())


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_get_price_data_pivoted())