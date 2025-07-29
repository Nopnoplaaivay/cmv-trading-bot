import datetime
import pytz


class TimeUtils:
    @classmethod
    def get_current_vn_time(cls):
        utcnow = datetime.datetime.now()
        return pytz.timezone('Asia/Ho_Chi_Minh').utcoffset(utcnow) + utcnow

    @classmethod
    def get_utc_current_time(cls):
        return datetime.datetime.now(datetime.timezone.utc)