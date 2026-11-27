from datetime import datetime
from uuid import UUID, uuid4

from db import Base
from sqlalchemy import UUID as SQLUUID
from sqlalchemy import String, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column


class Users(Base):
    __tablename__ = "users"
    id: Mapped[UUID] = mapped_column(
        SQLUUID, primary_key=True, nullable=False, default=uuid4
    )
    name: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    email: Mapped[str] = mapped_column(
        String(255), nullable=False, index=True, unique=True
    )
    hashed_pwd: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
