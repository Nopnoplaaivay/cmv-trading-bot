from sqlalchemy import Column, Integer, String, ForeignKey

from backend.common.consts import SQLServerConsts
from backend.modules.base.entities import Base



class OptimizedWeights(Base):
    __tablename__ = 'optimizedWeights'
    __table_args__ = (
        {"schema": SQLServerConsts.PORTFOLIO_SCHEMA},
        )
    __sqlServerType__ = f"[{SQLServerConsts.PORTFOLIO_SCHEMA}].[{__tablename__}]"

    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True, index=True)
    available_cash = Column(Integer, nullable=False)
    securing_amount = Column(Integer, nullable=False)
    purchasing_power = Column(Integer, nullable=False)
    user_id = Column(String, ForeignKey(f"{SQLServerConsts.AUTH_SCHEMA}.[users].[id]"), nullable=False)