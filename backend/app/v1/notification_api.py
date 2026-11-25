from datetime import datetime
from uuid import UUID

from db import get_db
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict, Field
from schemas import NotificationReadStatus, User
from services import (
    count_unread_notifications_handler,
    get_current_user,
    list_notification_handler,
    mark_batch_notifications_read_handler,
    mark_notification_read_handler,
)
from sqlalchemy.ext.asyncio import AsyncSession


class NotificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    message: str
    created_at: datetime
    read_at: datetime | None


class BatchNotificationReadRequest(BaseModel):
    notification_ids: list[UUID] = Field(max_length=100)


class UnreadNotificationCountResponse(BaseModel):
    unread_count: int


notif_router = APIRouter(prefix="/api/v1/notifications")


@notif_router.get("")
async def get_all_notifications(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    read_status: NotificationReadStatus = NotificationReadStatus.UNREAD,
) -> list[NotificationResponse]:
    notifications = await list_notification_handler(
        user.id, session, limit, offset, read_status=read_status
    )
    return [
        NotificationResponse.model_validate(item) for item in notifications
    ]


@notif_router.get("/unread-count")
async def get_unread_notification_count(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> UnreadNotificationCountResponse:
    unread_count = await count_unread_notifications_handler(user.id, session)
    return UnreadNotificationCountResponse(unread_count=unread_count)


@notif_router.patch("/{id}/read")
async def mark_notification_read(
    id: UUID,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> NotificationResponse:
    notification = await mark_notification_read_handler(user.id, id, session)
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="no notification found",
        )
    await session.commit()
    return NotificationResponse.model_validate(notification)


@notif_router.patch("/read")
async def mark_notification_batch_read(
    request: BatchNotificationReadRequest,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> list[UUID]:
    updated_ids = await mark_batch_notifications_read_handler(
        user.id, request.notification_ids, session
    )
    await session.commit()
    return list(updated_ids)
