from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.notifications.models import NotificationType


class NotificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    notification_type: NotificationType
    title: str
    message: str
    reference_id: UUID | None
    reference_type: str | None
    is_read: bool
    created_at: datetime