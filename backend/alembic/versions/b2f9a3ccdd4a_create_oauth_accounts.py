"""create OAuth accounts

Revision ID: b2f9a3ccdd4a
Revises: 36e1ccd6c65b
Create Date: 2026-11-27

"""

import sqlalchemy as sa

from alembic import op

revision = "b2f9a3ccdd4a"
down_revision = "36e1ccd6c65b"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "oauth_accounts",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("provider", sa.String(32), nullable=False),
        sa.Column("provider_user_id", sa.String(255), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("provider", "provider_user_id"),
    )
    op.create_index(
        op.f("ix_oauth_accounts_user_id"), "oauth_accounts", ["user_id"]
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(
        op.f("ix_oauth_accounts_user_id"), table_name="oauth_accounts"
    )
    op.drop_table("oauth_accounts")
