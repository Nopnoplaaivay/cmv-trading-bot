from sqlalchemy import Column, Integer, String, ForeignKey, DateTime

from backend.common.consts import SQLServerConsts
from backend.modules.base.entities import Base



class Sessions(Base):
    __tablename__ = 'sessions'
    __table_args__ = (
        {"schema": SQLServerConsts.AUTH_SCHEMA},
        )
    __sqlServerType__ = f"[{SQLServerConsts.AUTH_SCHEMA}].[{__tablename__}]"

    id = Column(String, primary_key=True, index=True, nullable=False)
    created_at = Column(String, nullable=False)
    updated_at = Column(String, nullable=False)
    signature = Column(String, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    role = Column(String)
    userId = Column(Integer, ForeignKey(f'[{SQLServerConsts.AUTH_SCHEMA}].[user].[id]', ondelete='CASCADE'), nullable=False)