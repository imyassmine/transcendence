from uuid import UUID

from db import Base
from schemas import EventType
from sqlalchemy import UUID as SQLUUID, String
from sqlalchemy.orm import Mapped, mapped_column


class Events(Base):
    __tablename__ = "events"
    id: Mapped[UUID] = mapped_column(
        SQLUUID, primary_key=True, index=True, nullable=False
    )
    type: Mapped[EventType] = mapped_column(
        String(50), index=True, nullable=False
    )
