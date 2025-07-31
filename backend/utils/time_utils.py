import datetime
import pytz
import os


class TimeUtils:
    @classmethod
    def get_current_vn_time(cls):
        utcnow = datetime.datetime.now()
        dev_time = utcnow # Timestamp in UTC for development
        prod_time = utcnow + pytz.timezone('Asia/Ho_Chi_Minh').utcoffset(utcnow) 
        return dev_time if os.getenv("TEST") == "1" else prod_time