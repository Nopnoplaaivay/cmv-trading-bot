from sqlalchemy import Column, Integer, String, Enum as SQLAlchemyEnum
from sqlalchemy.orm import relationship
from enum import Enum

from backend.common.consts import SQLServerConsts
from backend.modules.base.entities import Base


class Role(Enum):
    ADMIN = "admin"
    CLIENT = "client"


class Users(Base):
    __tablename__ = 'users'
    __table_args__ = (
        {"schema": SQLServerConsts.AUTH_SCHEMA},
        )
    __sqlServerType__ = f"[{SQLServerConsts.AUTH_SCHEMA}].[{__tablename__}]"
    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True, index=True)
    account = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)
    role = Column(SQLAlchemyEnum(Role), default=Role.CLIENT)
    mobile = Column(String, nullable=True)
    email = Column(String, nullable=True)
    sessions = relationship('Sessions', back_populates='user', cascade='all, delete-orphan')
    accounts = relationship('Accounts', back_populates='user', cascade='all, delete-orphan')