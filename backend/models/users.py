from uuid import UUID

from db import Base
from sqlalchemy import UUID as SQLUUID, String
from sqlalchemy.orm import Mapped, mapped_column


class Users(Base):
    __tablename__ = "users"
    id: Mapped[UUID] = mapped_column(
        SQLUUID, primary_key=True, index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(
        String(50), index=True, nullable=False
    )
