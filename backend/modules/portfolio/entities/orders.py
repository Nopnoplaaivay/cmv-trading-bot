from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship

from backend.common.consts import SQLServerConsts
from backend.modules.base.entities import Base


class Orders(Base):
    __tablename__ = "orders"
    __table_args__ = ({"schema": SQLServerConsts.PORTFOLIO_SCHEMA},)
    __sqlServerType__ = f"[{SQLServerConsts.PORTFOLIO_SCHEMA}].[{__tablename__}]"

    id = Column(String(36), primary_key=True, nullable=False, index=True)
    accountId = Column(
        String(36),
        ForeignKey(f"{SQLServerConsts.PORTFOLIO_SCHEMA}.accounts.id"),
        nullable=False,
    )
    brokerAccountId = Column(String(20), nullable=True)
    side = Column(String(10), nullable=False)
    symbol = Column(String(10), nullable=False)
    price = Column(Integer, nullable=False)
    quantity = Column(Integer, nullable=False)
    orderType = Column(String(10), nullable=False)
    orderStatus = Column(String(10), nullable=False)
    fillQuantity = Column(Integer, nullable=True)
    lastQuantity = Column(Integer, nullable=True)
    lastPrice = Column(Integer, nullable=True)
    averagePrice = Column(Integer, nullable=True)
    transDate = Column(String(30), nullable=True)
    createdDate = Column(String(30), nullable=True)
    modifiedDate = Column(String(30), nullable=True)
    leaveQuantity = Column(Integer, nullable=True)
    canceledQuantity = Column(Integer, nullable=True)
    priceSecure = Column(Integer, nullable=True)
    error = Column(String(255), nullable=True)

    # Relationships
    account = relationship("Accounts", back_populates="orders")
