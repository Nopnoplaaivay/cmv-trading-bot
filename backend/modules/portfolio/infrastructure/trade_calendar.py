from datetime import datetime, timedelta
from backend.utils.time_utils import TimeUtils
from backend.utils.logger import LOGGER

class TradingCalendarService:
    @staticmethod
    def is_trading_day(date: datetime) -> bool:
        return date.weekday() < 5

    @staticmethod
    def get_last_trading_date(current_date: datetime) -> datetime:
        check_date = current_date - timedelta(days=1)
        while not TradingCalendarService.is_trading_day(check_date):
            check_date -= timedelta(days=1)
        return check_date

    @staticmethod
    def get_next_trading_date(current_date: datetime) -> datetime:
        check_date = current_date + timedelta(days=1)
        while not TradingCalendarService.is_trading_day(check_date):
            check_date += timedelta(days=1)
        return check_date
    
    @classmethod
    def get_last_next_trading_dates(cls) -> tuple[datetime, datetime]:

        current_date = TimeUtils.get_current_vn_time()

        if not cls.is_trading_day(current_date):
            LOGGER.info(f"Today ({current_date.strftime('%A %d/%m/%Y')}) is not a trading day. Skipping notification.")
            return None, None
        
        current_hour = current_date.hour
        if current_hour >= 17:
            last_trading_date = current_date
            next_trading_date = cls.get_next_trading_date(current_date)
        elif current_hour < 15:
            last_trading_date = cls.get_last_trading_date(current_date)
            next_trading_date = current_date
    
    
    
        return last_trading_date, next_trading_date
