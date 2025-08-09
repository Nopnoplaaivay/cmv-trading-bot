from sqlalchemy import Column, Integer, String, Boolean

from backend.common.consts import SQLServerConsts
from backend.modules.base.entities import Base


class PortfolioMetadata(Base):
    __tablename__ = "portfolioMetadata"
    __table_args__ = ({"schema": SQLServerConsts.PORTFOLIO_SCHEMA},)
    __sqlServerType__ = f"[{SQLServerConsts.PORTFOLIO_SCHEMA}].[{__tablename__}]"

    id = Column(
        Integer, primary_key=True, nullable=False, autoincrement=True, index=True
    )
    portfolioId = Column(String, nullable=False)
    userId = Column(Integer, nullable=True)
    portfolioName = Column(String, nullable=False)
    portfolioType = Column(String)
    portfolioDesc = Column(String)
    algorithm = Column(String)
    isActive = Column(Boolean, default=True)