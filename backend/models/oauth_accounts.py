from datetime import datetime
from uuid import UUID, uuid4

from db import Base
from sqlalchemy import UUID as SQLUUID, func
from sqlalchemy import String, UniqueConstraint, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column


class OAuthAccounts(Base):
    __tablename__ = "oauth_accounts"
    __table_args__ = (UniqueConstraint("provider", "provider_user_id"),)
    # Un même fournisseur ne peut pas contenir deux mêmes identifiants
    id: Mapped[UUID] = mapped_column(
        SQLUUID, primary_key=True, nullable=False, default=uuid4
    )
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey(
            "users.id", ondelete="CASCADE"
        ),  # établit le lien entre user_id et la colonne id de la table users et ondelete="CASCADE" signifie que si un utilisateur est supprimé de la table users, les associations OAuth correspondantes sont également supprimées.
        index=True,
        nullable=False,
    )
    provider: Mapped[str] = mapped_column(String(32), nullable=False)
    provider_user_id: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
