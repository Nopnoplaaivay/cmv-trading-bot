from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship

from backend.common.consts import SQLServerConsts
from backend.modules.base.entities import Base


class Sessions(Base):
    __tablename__ = "sessions"
    __table_args__ = ({"schema": SQLServerConsts.AUTH_SCHEMA},)
    __sqlServerType__ = f"[{SQLServerConsts.AUTH_SCHEMA}].[{__tablename__}]"

    id = Column(String, primary_key=True, index=True, nullable=False)
    signature = Column(String, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    role = Column(String)
    userId = Column(
        Integer,
        ForeignKey(f"{SQLServerConsts.AUTH_SCHEMA}.users.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Relationship
    user = relationship("Users", back_populates="sessions")
