from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship

from backend.common.consts import SQLServerConsts
from backend.modules.base.entities import Base


class PersonalWeights(Base):
    __tablename__ = "personal_weights"
    __table_args__ = ({"schema": SQLServerConsts.PORTFOLIO_SCHEMA},)
    __sqlServerType__ = f"[{SQLServerConsts.PORTFOLIO_SCHEMA}].[{__tablename__}]"

    id = Column(String(36), primary_key=True, nullable=False, index=True)
    accountId = Column(
        String(36),
        ForeignKey(f"{SQLServerConsts.PORTFOLIO_SCHEMA}.accounts.id"),
        nullable=False,
    )
    date = Column(String(10), nullable=False)
    symbol = Column(String(10), nullable=False)
    targetWeight = Column(Integer, nullable=False)
    actualWeight = Column(Integer, nullable=False)

    # Relationships
    account = relationship("Accounts", back_populates="personal_weights")

