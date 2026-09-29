from uuid import UUID

from sqlalchemy.orm import Session

from app.notifications.models import Notification, NotificationType
from app.notifications.repository import NotificationRepository


class NotificationService:

    @staticmethod
    def create(
        db: Session,
        *,
        user_id: UUID,
        notification_type: NotificationType,
        title: str,
        message: str,
        reference_id: UUID | None = None,
        reference_type: str | None = None,
    ) -> Notification:

        notification = Notification(
            user_id=user_id,
            notification_type=notification_type,
            title=title,
            message=message,
            reference_id=reference_id,
            reference_type=reference_type,
            is_read=False,
        )

        return NotificationRepository.create(db, notification)

    @staticmethod
    def get_my_notifications(
        db: Session,
        user_id: UUID,
        unread_only: bool = False,
    ) -> list[Notification]:

        return NotificationRepository.get_user_notifications(
            db,
            user_id,
            unread_only,
        )

    @staticmethod
    def mark_as_read(
        db: Session,
        notification_id: UUID,
        user_id: UUID,
    ) -> Notification:

        notification = NotificationRepository.get_by_id(
            db,
            notification_id,
        )

        if not notification:
            raise ValueError("Notification not found.")

        # Critical: user can only modify their own notification.
        if notification.user_id != user_id:
            raise PermissionError("You cannot modify this notification.")

        NotificationRepository.mark_as_read(db, notification)

        return notification

    @staticmethod
    def mark_all_as_read(
        db: Session,
        user_id: UUID,
    ) -> None:

        NotificationRepository.mark_all_as_read(
            db,
            user_id,
        )