from datetime import datetime

from db import Base
from sqlalchemy import Boolean, DateTime, Float, Index, String, Text, func # type: ignore
from sqlalchemy.dialects.postgresql import JSONB # type: ignore
from sqlalchemy.orm import Mapped, mapped_column # type: ignore


class DeletionLinkCache(Base):
    __tablename__ = "deletion_links"
    __table_args__ = (Index("ix_deletion_links_checked_at", "checked_at"),)
    domain: Mapped[str] = mapped_column(String(255), primary_key=True)
    service: Mapped[str | None] = mapped_column(String(100), nullable=True)
    url: Mapped[str | None] = mapped_column(Text, nullable=True)
    kind: Mapped[str] = mapped_column(String(20), nullable=False)
    probability: Mapped[float] = mapped_column(Float, nullable=False)
    confident: Mapped[bool] = mapped_column(Boolean, nullable=False)
    verified: Mapped[bool] = mapped_column(Boolean, nullable=False)
    source: Mapped[str] = mapped_column(String(100), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    alternatives: Mapped[list[str]] = mapped_column(
        JSONB, nullable=False, default=list
    )
    contact_email: Mapped[str | None] = mapped_column(
        String(255), nullable=True
    )
    contact_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    contact_checked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    checked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
