import datetime
from sqlalchemy import Column, Integer, String, Float
from typing import Optional, Dict, Any

from backend.common.consts import SQLServerConsts
from backend.modules.base.entities import Base
from backend.utils.time_utils import TimeUtils


class TradingTokens(Base):
    __tablename__ = "tradingTokens"
    __table_args__ = ({"schema": SQLServerConsts.BROKERS_SCHEMA},)
    __sqlServerType__ = f"[{SQLServerConsts.BROKERS_SCHEMA}].[{__tablename__}]"

    id = Column(String, primary_key=True, index=True, nullable=False)
    account = Column(String, nullable=False, index=True)
    jwtToken = Column(String, nullable=False)
    tradingToken = Column(String)
    broker = Column(String, nullable=False)
    createdAt = Column(String)
    updatedAt = Column(String)

    def is_valid(self) -> bool:
        try:
            if not self.updatedAt:
                return False

            expire_at = datetime.datetime.strptime(
                self.updatedAt, SQLServerConsts.TRADING_TIME_FORMAT
            ) + datetime.timedelta(hours=6)
            return TimeUtils.get_current_vn_time() < expire_at
        except (ValueError, TypeError):
            return False

    def time_remaining(self) -> Optional[datetime.timedelta]:
        if not self.updatedAt:
            return None
        expire_at = datetime.datetime.strptime(
            self.updatedAt, SQLServerConsts.TRADING_TIME_FORMAT
        ) + datetime.timedelta(hours=6)
        remaining = expire_at - TimeUtils.get_current_vn_time()
        return remaining if remaining > datetime.timedelta(0) else None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "account": self.account,
            "jwtToken": self.jwtToken,
            "tradingToken": self.tradingToken,
            "broker": self.broker,
            "createdAt": self.createdAt,
            "updatedAt": self.updatedAt,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TradingTokens":
        return cls(
            id=data.get("id"),
            account=data.get("account"),
            jwtToken=data.get("jwtToken"),
            tradingToken=data.get("tradingToken"),
            broker=data.get("broker"),
            createdAt=data.get("createdAt"),
            updatedAt=data.get("updatedAt"),
        )
    


    def __repr__(self) -> str:
        return f"<TradingTokens(id={self.id}, account='{self.account}', broker='{self.broker}', valid={self.is_valid()})>"
