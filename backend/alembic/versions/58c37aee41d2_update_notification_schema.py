"""Update notification schema to store event IDs and rendered messages."""

from alembic import op
import sqlalchemy as sa


revision = "58c37aee41d2"
down_revision = "176d7c803dfb"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "events",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("type", sa.String(50), nullable=False),
    )
    op.create_index("ix_events_id", "events", ["id"])
    op.create_index("ix_events_type", "events", ["type"])

    op.alter_column("notifications", "rescource_type", new_column_name="event_type")
    op.add_column("notifications", sa.Column("event_id", sa.UUID()))
    op.add_column("notifications", sa.Column("title", sa.String(50)))
    op.add_column("notifications", sa.Column("message", sa.String(500)))
    op.add_column("notifications", sa.Column("meta_data", sa.JSON()))
    op.alter_column("notifications", "read_at", nullable=True, server_default=None)

    # Older rows have no event ID or rendered text. Their notification IDs
    # provide a stable, distinct identifier for each backfilled event.
    op.execute("INSERT INTO events (id, type) SELECT id, event_type FROM notifications")
    op.execute(
        """
        UPDATE notifications
        SET event_id = id,
            title = 'Notification',
            message = 'Recorded action: ' || type,
            read_at = CASE WHEN is_read THEN read_at ELSE NULL END
        """
    )

    op.alter_column("notifications", "event_id", nullable=False)
    op.alter_column("notifications", "title", nullable=False)
    op.alter_column("notifications", "message", nullable=False)
    op.create_foreign_key(
        "fk_notifications_event_id", "notifications", "events", ["event_id"], ["id"]
    )
    op.create_index("ix_notifications_event_id", "notifications", ["event_id"], unique=True)
    op.drop_column("notifications", "is_read")


def downgrade() -> None:
    op.add_column("notifications", sa.Column("is_read", sa.Boolean()))
    op.execute(
        """
        UPDATE notifications
        SET is_read = read_at IS NOT NULL,
            read_at = COALESCE(read_at, created_at)
        """
    )
    op.alter_column("notifications", "is_read", nullable=False)
    op.alter_column("notifications", "read_at", nullable=False, server_default=sa.func.now())
    op.drop_index("ix_notifications_event_id", table_name="notifications")
    op.drop_constraint("fk_notifications_event_id", "notifications", type_="foreignkey")
    op.drop_column("notifications", "meta_data")
    op.drop_column("notifications", "message")
    op.drop_column("notifications", "title")
    op.drop_column("notifications", "event_id")
    op.alter_column("notifications", "event_type", new_column_name="rescource_type")
    op.drop_table("events")
