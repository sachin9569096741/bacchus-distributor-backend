from uuid import UUID, uuid4

from sqlalchemy.orm import Session

from app.audit.models import AuditLog
from app.audit.repository import AuditRepository


class AuditService:

    @staticmethod
    def log(
        db: Session,
        *,
        actor_id: UUID | None,
        action: str,
        entity: str,
        entity_id: UUID | None = None,
        ip_address: str | None = None,
        old_value: dict | None = None,
        new_value: dict | None = None,
    ) -> AuditLog:
        """
        Create an immutable audit event.

        This method only creates the audit record and flushes it.
        The caller controls the surrounding transaction.
        """

        audit_log = AuditLog(
            id=uuid4(),
            actor_id=actor_id,
            action=action,
            entity=entity,
            entity_id=entity_id,
            ip_address=ip_address,
            old_value=old_value,
            new_value=new_value,
        )

        return AuditRepository.create(
            db,
            audit_log,
        )

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

        return AuditRepository.list_logs(
            db,
            actor_id=actor_id,
            action=action,
            entity=entity,
            entity_id=entity_id,
            limit=limit,
            offset=offset,
        )

    @staticmethod
    def get_by_id(
        db: Session,
        audit_log_id: UUID,
    ) -> AuditLog | None:

        return AuditRepository.get_by_id(
            db,
            audit_log_id,
        )