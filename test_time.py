import datetime
import pytz

from backend.utils.time_utils import TimeUtils

print(TimeUtils.get_current_vn_time())
utcnow = datetime.datetime.now()
print(utcnow)
print(pytz.timezone('Asia/Ho_Chi_Minh').utcoffset(utcnow))