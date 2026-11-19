from datetime import datetime
from uuid import UUID

from db import Base
from pydantic import JsonValue
from schemas import EventType, NotificationType
from sqlalchemy import JSON, UUID as SQLUUID, DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column


class Notifications(Base):
    __tablename__ = "notifications"
    id: Mapped[UUID] = mapped_column(
        SQLUUID, primary_key=True, index=True, nullable=False
    )
    title: Mapped[str] = mapped_column(String(50), nullable=False)
    message: Mapped[str] = mapped_column(String(500), nullable=False)
    type: Mapped[NotificationType] = mapped_column(String(20), nullable=False)
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    event_id: Mapped[UUID] = mapped_column(
        SQLUUID,
        ForeignKey("events.id"),
        index=True,
        nullable=False,
        unique=True,
    )
    event_type: Mapped[EventType] = mapped_column(String(20), nullable=False)
    meta_data: Mapped[dict[str, JsonValue] | None] = mapped_column(
        JSON, default=dict
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    read_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
