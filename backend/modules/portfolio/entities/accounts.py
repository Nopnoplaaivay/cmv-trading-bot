from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship

from backend.common.consts import SQLServerConsts
from backend.modules.base.entities import Base


class Accounts(Base):
    __tablename__ = "accounts"
    __table_args__ = ({"schema": SQLServerConsts.PORTFOLIO_SCHEMA},)
    __sqlServerType__ = f"[{SQLServerConsts.PORTFOLIO_SCHEMA}].[{__tablename__}]"

    id = Column(String(36), primary_key=True, nullable=False, index=True)
    userId = Column(
        Integer, ForeignKey(f"{SQLServerConsts.AUTH_SCHEMA}.users.id"), nullable=False
    )
    name = Column(String(50), nullable=False)
    accountType = Column(String(20), nullable=True)
    identificationCode = Column(String(20), nullable=True)
    custodyCode = Column(String(20), nullable=False)
    password = Column(String(255), nullable=False)  
    brokerName = Column(String(20), nullable=True)
    brokerInvestorId = Column(String(20), nullable=False)
    brokerAccountId = Column(String(20), nullable=False)

    # Relationships
    user = relationship("Users", back_populates="accounts")
    balances = relationship("Balances", back_populates="account", cascade="all, delete-orphan")
    orders = relationship("Orders", back_populates="account", cascade="all, delete-orphan")
    deals = relationship("Deals", back_populates="account", cascade="all, delete-orphan")
    personal_weights = relationship("PersonalWeights", back_populates="account", cascade="all, delete-orphan")
