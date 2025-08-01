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
    
    jwtCreatedAt = Column(String)      # When JWT was created
    tradingCreatedAt = Column(String)  # When trading token was created
    createdAt = Column(String)         # When record was first created
    updatedAt = Column(String)         # When record was last updated

    def is_jwt_valid(self) -> bool:
        try:
            if not self.jwtCreatedAt:
                return False
            
            jwt_expire_at = datetime.datetime.strptime(
                self.jwtCreatedAt, SQLServerConsts.TRADING_TIME_FORMAT
            ) + datetime.timedelta(hours=7)
            
            return TimeUtils.get_current_vn_time() < jwt_expire_at
        except (ValueError, TypeError):
            return False
    
    def is_trading_token_valid(self) -> bool:
        try:
            if not self.tradingCreatedAt or not self.tradingToken:
                return False
            
            trading_expire_at = datetime.datetime.strptime(
                self.tradingCreatedAt, SQLServerConsts.TRADING_TIME_FORMAT
            ) + datetime.timedelta(hours=7)
            
            return TimeUtils.get_current_vn_time() < trading_expire_at
        except (ValueError, TypeError):
            return False

    def is_valid(self) -> bool:
        return self.is_jwt_valid() and self.is_trading_token_valid()
    
    def is_partially_valid(self) -> bool:
        return self.is_jwt_valid()

    def jwt_time_remaining(self) -> Optional[datetime.timedelta]:
        if not self.jwtCreatedAt:
            return None
        try:
            jwt_expire_at = datetime.datetime.strptime(
                self.jwtCreatedAt, SQLServerConsts.TRADING_TIME_FORMAT
            ) + datetime.timedelta(hours=6)
            
            remaining = jwt_expire_at - TimeUtils.get_current_vn_time()
            return remaining if remaining > datetime.timedelta(0) else None
        except (ValueError, TypeError):
            return None

    def trading_time_remaining(self) -> Optional[datetime.timedelta]:
        if not self.tradingCreatedAt:
            return None
        try:
            trading_expire_at = datetime.datetime.strptime(
                self.tradingCreatedAt, SQLServerConsts.TRADING_TIME_FORMAT
            ) + datetime.timedelta(hours=6)
            
            remaining = trading_expire_at - TimeUtils.get_current_vn_time()
            return remaining if remaining > datetime.timedelta(0) else None
        except (ValueError, TypeError):
            return None

    def time_remaining(self) -> Optional[datetime.timedelta]:
        jwt_remaining = self.jwt_time_remaining()
        trading_remaining = self.trading_time_remaining()
        
        if jwt_remaining and trading_remaining:
            return min(jwt_remaining, trading_remaining)
        elif jwt_remaining:
            return jwt_remaining
        elif trading_remaining:
            return trading_remaining
        else:
            return None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "account": self.account,
            "jwtToken": self.jwtToken,
            "tradingToken": self.tradingToken,
            "broker": self.broker,
            "jwtCreatedAt": self.jwtCreatedAt,
            "tradingCreatedAt": self.tradingCreatedAt,
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
            jwtCreatedAt=data.get("jwtCreatedAt"),
            tradingCreatedAt=data.get("tradingCreatedAt"),
            createdAt=data.get("createdAt"),
            updatedAt=data.get("updatedAt"),
        )
    


    def __repr__(self) -> str:
        return f"<TradingTokens(id={self.id}, account='{self.account}', broker='{self.broker}', valid={self.is_valid()})>"
