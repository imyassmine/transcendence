"""Store notification event identifiers on notifications."""

import sqlalchemy as sa
from alembic import op


revision = "722d64f537a1"
down_revision = "58c37aee41d2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("LOCK TABLE events, notifications IN ACCESS EXCLUSIVE MODE")
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1
                FROM events
                WHERE NOT EXISTS (
                    SELECT 1
                    FROM notifications
                    WHERE notifications.event_id = events.id
                        AND notifications.event_type = events.type
                )
            ) THEN
                RAISE EXCEPTION 'The events table contains records without an equivalent notification';
            END IF;
        END
        $$;
        """
    )
    op.drop_constraint("fk_notifications_event_id", "notifications", type_="foreignkey")
    op.drop_table("events")


def downgrade() -> None:
    op.create_table(
        "events",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("type", sa.String(50), nullable=False),
    )
    op.create_index("ix_events_id", "events", ["id"])
    op.create_index("ix_events_type", "events", ["type"])
    op.execute("INSERT INTO events (id, type) SELECT event_id, event_type FROM notifications")
    op.create_foreign_key(
        "fk_notifications_event_id", "notifications", "events", ["event_id"], ["id"]
    )
