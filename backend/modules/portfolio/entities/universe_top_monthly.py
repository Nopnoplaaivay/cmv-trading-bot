from sqlalchemy import Column, Integer, String, Float

from backend.common.consts import SQLServerConsts
from backend.modules.base.entities import Base



class UniverseTopMonthly(Base):
    __tablename__ = 'universeTopMonthly'
    __table_args__ = (
        {"schema": SQLServerConsts.PORTFOLIO_SCHEMA},
        )
    __sqlServerType__ = f"[{SQLServerConsts.PORTFOLIO_SCHEMA}].[{__tablename__}]"

    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True, index=True)
    year = Column(Integer, nullable=False)
    month = Column(Integer, nullable=False)
    symbol = Column(String, nullable=False)
    exchangeCode = Column(String, nullable=True)
    sectorL2 = Column(String, nullable=True)
    cap = Column(Float, nullable=True)
    averageLiquidity21 = Column(Float, nullable=True)
    averageLiquidity63 = Column(Float, nullable=True)
    averageLiquidity252 = Column(Float, nullable=True)
    grossProfitQoQ = Column(Float, nullable=True)
    roe = Column(Float, nullable=True)
    eps = Column(Float, nullable=True)
    pe = Column(Float, nullable=True)
    pb = Column(Float, nullable=True)