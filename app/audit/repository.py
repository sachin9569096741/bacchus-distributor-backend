from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.audit.models import AuditLog


class AuditRepository:

    @staticmethod
    def create(
        db: Session,
        audit_log: AuditLog,
    ) -> AuditLog:
        db.add(audit_log)
        db.flush()
        return audit_log

    @staticmethod
    def get_by_id(
        db: Session,
        audit_log_id: UUID,
    ) -> AuditLog | None:
        stmt = select(AuditLog).where(
            AuditLog.id == audit_log_id
        )
        return db.scalar(stmt)

    @staticmethod
    def list_logs(
        db: Session,
        *,
        actor_id: UUID | None = None,
        action: str | None = None,
        entity: str | None = None,
        entity_id: UUID | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[AuditLog]:

        stmt = select(AuditLog)

        if actor_id is not None:
            stmt = stmt.where(AuditLog.actor_id == actor_id)

        if action is not None:
            stmt = stmt.where(AuditLog.action == action)

        if entity is not None:
            stmt = stmt.where(AuditLog.entity == entity)

        if entity_id is not None:
            stmt = stmt.where(AuditLog.entity_id == entity_id)

        stmt = (
            stmt
            .order_by(AuditLog.created_at.desc())
            .offset(offset)
            .limit(limit)
        )

        return list(db.scalars(stmt).all())