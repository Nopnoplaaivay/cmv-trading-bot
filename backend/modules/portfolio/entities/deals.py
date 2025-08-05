from sqlalchemy import Column, Integer, String, ForeignKey, Float
from sqlalchemy.orm import relationship

from backend.common.consts import SQLServerConsts
from backend.modules.base.entities import Base


class Deals(Base):
    __tablename__ = "deals"
    __table_args__ = ({"schema": SQLServerConsts.PORTFOLIO_SCHEMA},)
    __sqlServerType__ = f"[{SQLServerConsts.PORTFOLIO_SCHEMA}].[{__tablename__}]"

    id = Column(String(36), primary_key=True, nullable=False, index=True)
    brokerAccountId = Column(
        String(20),
        ForeignKey(f"{SQLServerConsts.PORTFOLIO_SCHEMA}.accounts.brokerAccountId"),
        nullable=False,
    )
    dealId = Column(String(10), nullable=False, index=True)
    symbol = Column(String(10), nullable=False, index=True)
    status = Column(String(10), nullable=True)
    side = Column(String(10), nullable=True)
    secure = Column(Float, nullable=True)
    accumulateQuantity = Column(Integer, nullable=False)
    tradeQuantity = Column(Integer, nullable=False)
    closedQuantity = Column(Integer, nullable=False)
    t0ReceivingQuantity = Column(Integer, nullable=True)
    t1ReceivingQuantity = Column(Integer, nullable=True)
    t2ReceivingQuantity = Column(Integer, nullable=True)
    costPrice = Column(Float, nullable=False)
    averageCostPrice = Column(Float, nullable=False)
    marketPrice = Column(Float, nullable=False)
    realizedProfit = Column(Float, nullable=False)
    unrealizedProfit = Column(Float, nullable=True)
    breakEvenPrice = Column(Float, nullable=True)
    dividendReceivingQuantity = Column(Integer, nullable=True)
    dividendQuantity = Column(Integer, nullable=True)
    cashReceiving = Column(Float, nullable=True)
    rightReceivingCash = Column(Integer, nullable=True)
    t0ReceivingCash = Column(Float, nullable=True)
    t1ReceivingCash = Column(Float, nullable=True)
    t2ReceivingCash = Column(Float, nullable=True)
    createdDate = Column(String(30), nullable=True)
    modifiedDate = Column(String(30), nullable=True)
    
    # Relationships
    account = relationship("Accounts", back_populates="deals")


