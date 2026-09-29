from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.audit.schemas import AuditLogResponse
from app.audit.service import AuditService
from app.core.dependencies import get_current_user, get_database
from app.permissions.dependencies import require_any_role
from app.users.models import User

router = APIRouter(
    prefix="/audit-logs",
    tags=["Audit Logs"],
)


def _admin_only():
    return require_any_role("SUPER ADMIN", "MASTER ADMIN")


@router.get(
    "",
    response_model=list[AuditLogResponse],
    dependencies=[Depends(_admin_only())],
)
def list_audit_logs(
    actor_id: UUID | None = Query(default=None),
    action: str | None = Query(default=None, max_length=100),
    entity: str | None = Query(default=None, max_length=100),
    entity_id: UUID | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user),
):
    return AuditService.list_logs(
        db,
        actor_id=actor_id,
        action=action,
        entity=entity,
        entity_id=entity_id,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/{audit_log_id}",
    response_model=AuditLogResponse,
    dependencies=[Depends(_admin_only())],
)
def get_audit_log(
    audit_log_id: UUID,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user),
):
    audit_log = AuditService.get_by_id(db, audit_log_id)

    if audit_log is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audit log not found",
        )

    return audit_log
