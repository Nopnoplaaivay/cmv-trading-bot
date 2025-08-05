import os
import datetime

class SQLServerConsts:
    AUTH_SCHEMA = "BotAuth"
    PORTFOLIO_SCHEMA = "BotPortfolio"
    BROKERS_SCHEMA = "BotBrokers"


    TRADING_TIME_FORMAT = "%Y-%m-%d %H:%M:%S"
    GMT_7_NOW = f"SWITCHOFFSET(SYSUTCDATETIME(), '+07:00')"
    GMT_7_NOW_VARCHAR = f"FORMAT(SWITCHOFFSET(SYSUTCDATETIME(), '+07:00'), 'yyyy-MM-dd HH:mm:ss')"

    DATE_FORMAT = "%Y-%m-%d"
    START_TRADING_MONTH = '2025-01'
    # START_TRADING_DAY = datetime.datetime.strptime(os.environ.get("START_TRADING_DAY", None), "%Y-%m-%d")
    START_TRADING_DAY = datetime.datetime.strptime('2025-01-01', "%Y-%m-%d")
    TRADING_DAY_FORMAT = "%Y-%m-%d"

class CommonConsts:
    ROOT_FOLDER = os.path.abspath(os.path.join(os.path.abspath(__file__), 3 * "../"))

    SALT = os.getenv("SALT")
    AT_SECRET_KEY = os.getenv("AT_SECRET_KEY")
    RT_SECRET_KEY = os.getenv("RT_SECRET_KEY")
    ACCESS_TOKEN_EXPIRES_IN = 3600
    REFRESH_TOKEN_EXPIRES_IN = 86400

    DEBUG = os.getenv("DEBUG") 

class MessageConsts:
    CREATED = "Created"
    SUCCESS = "Success"
    VALIDATION_FAILED = "Validation failed"
    UNAUTHORIZED = "Unauthorized"
    BAD_REQUEST = "Bad request"
    FORBIDDEN = "Forbidden"
    NOT_FOUND = "Not found"
    CONFLICT = "Conflict"
    INVALID_OBJECT_ID = "Invalid object id"
    INVALID_INPUT = "Invalid input"
    INTERNAL_SERVER_ERROR = "Unknown internal server error"
    TRADING_API_ERROR = "Trading API error"

class DNSEConsts:
    BASE_URL = "https://api.dnse.com.vn"
    BROKER = 'datafeed-lts-krx.dnse.com.vn'
