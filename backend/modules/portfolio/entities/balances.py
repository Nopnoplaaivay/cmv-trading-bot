from sqlalchemy import Column, String, Integer, Float, ForeignKey
from sqlalchemy.orm import relationship

from backend.common.consts import SQLServerConsts
from backend.modules.base.entities import Base


class Balances(Base):
    __tablename__ = "balances"
    __table_args__ = ({"schema": SQLServerConsts.PORTFOLIO_SCHEMA},)
    __sqlServerType__ = f"[{SQLServerConsts.PORTFOLIO_SCHEMA}].[{__tablename__}]"

    id = Column(String(36), primary_key=True, nullable=False, index=True)
    brokerAccountId = Column(
        String(20),
        ForeignKey(f"{SQLServerConsts.PORTFOLIO_SCHEMA}.accounts.brokerAccountId"),
        nullable=False,
    )
    totalCash = Column(Integer, nullable=True)
    availableCash = Column(Integer, nullable=True)
    termDeposit = Column(Integer, nullable=True)
    depositInterest = Column(Integer, nullable=True)
    stockValue = Column(Integer, nullable=True)
    marginableAmount = Column(Integer, nullable=True)
    nonMarginableAmount = Column(Integer, nullable=True)
    totalDebt = Column(Integer, nullable=True)
    netAssetValue = Column(Integer, nullable=True)
    receivingAmount = Column(Integer, nullable=True)
    secureAmount = Column(Integer, nullable=True)
    depositFeeAmount = Column(Integer, nullable=True)
    maxLoanLimit = Column(Integer, nullable=True)
    withdrawableCash = Column(Integer, nullable=True)
    collateralValue = Column(Integer, nullable=True)
    orderSecured = Column(Integer, nullable=True)
    purchasingPower = Column(Integer, nullable=True)
    cashDividendReceiving = Column(Integer, nullable=True)
    marginDebt = Column(Float, nullable=True)
    marginRate = Column(Float, nullable=True)
    ppWithdraw = Column(Integer, nullable=True)
    blockMoney = Column(Integer, nullable=True)
    totalRemainDebt = Column(Float, nullable=True)
    totalUnrealizedDebt = Column(Float, nullable=True)
    blockedAmount = Column(Float, nullable=True)
    advancedAmount = Column(Integer, nullable=True)
    advanceWithdrawnAmount = Column(Float, nullable=True)

    # Relationships
    account = relationship("Accounts", back_populates="balances")
