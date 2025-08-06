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
print(pytz.timezone('Asia/Ho_Chi_Minh').utcoffset(utcnow))