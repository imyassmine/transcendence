from enum import StrEnum, auto
from uuid import UUID

from pydantic import AwareDatetime, BaseModel, Field, JsonValue


class EventType(StrEnum):
    ACCOUNT = auto()
    SCAN = auto()
    DRAFT = auto()


class NotificationType(StrEnum):
    ACCOUNT_CREATED = "account.created"
    ACCOUNT_UPDATED = "account.updated"
    ACCOUNT_DELETED = "account.deleted"
    SCAN_COMPLETED = "scan.completed"
    SCAN_FAILED = "scan.failed"
    DRAFT_CREATED = "draft.created"


class NotificationEvent(BaseModel):
    """Internal event with metadata supplied by the backend producer."""

    event_id: UUID
    user_id: UUID
    type: NotificationType
    created_at: AwareDatetime
    meta_data: dict[str, JsonValue] = Field(default_factory=dict)

    @property
    def event_type(self) -> EventType:
        return EventType(self.type.value.partition(".")[0])
