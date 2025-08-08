import datetime
import pytz
import os


class TimeUtils:
    @classmethod
    def get_current_vn_time(cls):
        utcnow = datetime.datetime.now()
        local_machine_time = utcnow # Timestamp in UTC for development
        docker_time = utcnow + pytz.timezone('Asia/Ho_Chi_Minh').utcoffset(utcnow) 
        return docker_time if os.getenv("DOCKER_TIME") == "1" else local_machine_time