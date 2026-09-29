from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.notifications.models import Notification


class NotificationRepository:

    @staticmethod
    def create(
        db: Session,
        notification: Notification,
    ) -> Notification:
        db.add(notification)
        db.flush()
        return notification

    @staticmethod
    def get_by_id(
        db: Session,
        notification_id: UUID,
    ) -> Notification | None:
        stmt = select(Notification).where(
            Notification.id == notification_id
        )
        return db.scalar(stmt)

    @staticmethod
    def get_user_notifications(
        db: Session,
        user_id: UUID,
        unread_only: bool = False,
    ) -> list[Notification]:
        stmt = (
            select(Notification)
            .where(Notification.user_id == user_id)
            .order_by(Notification.created_at.desc())
        )

        if unread_only:
            stmt = stmt.where(Notification.is_read.is_(False))

        return list(db.scalars(stmt).all())

    @staticmethod
    def mark_as_read(
        db: Session,
        notification: Notification,
    ) -> Notification:
        notification.is_read = True
        db.flush()
        return notification

    @staticmethod
    def mark_all_as_read(
        db: Session,
        user_id: UUID,
    ) -> None:
        stmt = (
            update(Notification)
            .where(
                Notification.user_id == user_id,
                Notification.is_read.is_(False),
            )
            .values(is_read=True)
        )

        db.execute(stmt)
        db.flush()