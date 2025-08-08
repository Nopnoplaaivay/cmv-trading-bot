from sqlalchemy import Column, Integer, String, Float

from backend.common.consts import SQLServerConsts
from backend.modules.base.entities import Base


class Portfolios(Base):
    __tablename__ = "portfolios"
    __table_args__ = ({"schema": SQLServerConsts.PORTFOLIO_SCHEMA},)
    __sqlServerType__ = f"[{SQLServerConsts.PORTFOLIO_SCHEMA}].[{__tablename__}]"

    id = Column(
        Integer, primary_key=True, nullable=False, autoincrement=True, index=True
    )
    date = Column(String, nullable=False)
    portfolioType = Column(String, nullable=True)
    portfolioId = Column(String, nullable=False)
    userId = Column(Integer, nullable=True)
    symbol = Column(String, nullable=False)
    marketPrice = Column(Float, nullable=False)
    initialWeight = Column(Float, nullable=False)
    neutralizedWeight = Column(Float, nullable=True)
    limitedWeight = Column(Float, nullable=True)
    neutralizedLimitedWeight = Column(Float, nullable=True)
    algorithm = Column(String, nullable=True)
