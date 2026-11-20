from typing import Sequence
from uuid import UUID, uuid4

from models import Notifications
from schemas import NotificationEvent, NotificationType
from sqlalchemy import func, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

ACCOUNT_NOTIFICATION_TEMPLATES = {
    NotificationType.ACCOUNT_CREATED: (
        "Add platform",
        "{platform_name} is added.",
    ),
    NotificationType.ACCOUNT_UPDATED: (
        "Account updated",
        "Your {platform_name} account details were updated.",
    ),
    NotificationType.ACCOUNT_DELETED: (
        "Account removed",
        "{platform_name} was removed from your account list.",
    ),
    NotificationType.SCAN_FAILED: (
        "Scan completed",
        "{platform_name} scan failed",
    ),
    NotificationType.SCAN_COMPLETED: (
        "Scan completed",
        "{platform_name} scan completed",
    ),
    NotificationType.DRAFT_CREATED: (
        "Draft created",
        "Email draft is created",
    ),
    NotificationType.DRAFT_SENT: ("Draft sent", "Email has been sent"),
}


async def create_notification_event_handler(
    notif: NotificationEvent, session: AsyncSession
) -> Notifications | None:
    template = ACCOUNT_NOTIFICATION_TEMPLATES.get(notif.type)
    if template is None:
        raise ValueError(f"Unsupported notification type: {notif.type}")

    platform_name = notif.meta_data.get("platform_name")
    if not isinstance(platform_name, str) or not platform_name.strip():
        raise ValueError(f"{notif.type} requires a non-empty platform_name")

    platform_name = platform_name.strip()
    title, message_template = template
    message = message_template.format(platform_name=platform_name)
    if len(message) > 500:
        raise ValueError("Notification message exceeds 500 characters")

    result = await session.scalars(
        insert(Notifications)
        .values(
            id=uuid4(),
            event_id=notif.event_id,
            user_id=notif.user_id,
            type=notif.type,
            event_type=notif.event_type,
            title=title,
            message=message,
            meta_data={"platform_name": platform_name},
        )
        .on_conflict_do_nothing(index_elements=[Notifications.event_id])
        .returning(Notifications)
    )
    return result.one_or_none()


async def list_notification_handler(
    user_id: UUID, session: AsyncSession, limit: int = 20, offset: int = 0
) -> Sequence[Notifications]:
    """List the user's unread notifications, newest first."""
    if not 1 <= limit <= 100:
        raise ValueError("limit must be between 1 and 100")
    if offset < 0:
        raise ValueError("offset must be non-negative")

    result = await session.scalars(
        select(Notifications)
        .where(
            Notifications.user_id == user_id, Notifications.read_at.is_(None)
        )
        .order_by(Notifications.created_at.desc(), Notifications.id.desc())
        .limit(limit)
        .offset(offset)
    )
    return result.all()


async def count_unread_notifications_handler(
    user_id: UUID, session: AsyncSession
) -> int:
    result = await session.execute(
        select(func.count())
        .select_from(Notifications)
        .where(
            Notifications.user_id == user_id, Notifications.read_at.is_(None)
        )
    )
    return result.scalar_one()


async def mark_notification_read_handler(
    user_id: UUID, notification_id: UUID, session: AsyncSession
) -> Notifications | None:

    result = await session.scalars(
        update(Notifications)
        .where(
            Notifications.id == notification_id,
            Notifications.user_id == user_id,
        )
        .values(read_at=func.coalesce(Notifications.read_at, func.now()))
        .returning(Notifications)
        .execution_options(populate_existing=True)
    )
    return result.one_or_none()


async def mark_batch_notifications_read_handler(
    user_id: UUID, notification_ids: list[UUID], session: AsyncSession
) -> Sequence[UUID]:
    result = await session.scalars(
        update(Notifications)
        .where(
            Notifications.user_id == user_id,
            Notifications.id.in_(notification_ids),
            Notifications.read_at.is_(None),
        )
        .values(read_at=func.now())
        .returning(Notifications.id)
    )
    return result.all()
