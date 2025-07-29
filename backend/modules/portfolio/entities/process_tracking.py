from sqlalchemy import Column, Integer, String, Float

from backend.common.consts import SQLServerConsts
from backend.modules.base.entities import Base


class ProcessTracking(Base):
    __tablename__ = "__processTracking__"
    __table_args__ = (
        {"schema": SQLServerConsts.PORTFOLIO_SCHEMA},
    )
    __sqlServerType__ = f"[{SQLServerConsts.PORTFOLIO_SCHEMA}].[{__tablename__}]"

    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True, index=True)
    schemaName = Column(String)
    tableName = Column(String)
    keyName = Column(String)
    keyValue = Column(String)