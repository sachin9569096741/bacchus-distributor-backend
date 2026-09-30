from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_database
from app.permissions.dependencies import require_role
from app.users.models import User
from app.users.schemas import (
    MasterAdminCreate,
    MasterAdminResponse,
    MasterAdminUpdate,
)
from app.users.service import (
    UserServiceError,
    create_master_admin,
    delete_master_admin,
    list_master_admins,
    update_master_admin,
)

router = APIRouter(
    prefix="/master-admins",
    tags=["Master Admins"],
)


# ============================================================
# CREATE MASTER ADMIN
# SUPER ADMIN ONLY
# ============================================================

@router.post(
    "",
    response_model=MasterAdminResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_master_admin_endpoint(
    data: MasterAdminCreate,
    db: Session = Depends(get_database),
    _: User = Depends(require_role("SUPER ADMIN")),
):
    try:
        return create_master_admin(db, data)

    except UserServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )


# ============================================================
# LIST MASTER ADMINS
# SUPER ADMIN ONLY
# ============================================================

@router.get(
    "",
    response_model=list[MasterAdminResponse],
)
def list_master_admins_endpoint(
    db: Session = Depends(get_database),
    _: User = Depends(require_role("SUPER ADMIN")),
):
    try:
        return list_master_admins(db)

    except UserServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )


# ============================================================
# UPDATE MASTER ADMIN
# SUPER ADMIN ONLY
# ============================================================

@router.patch(
    "/{user_id}",
    response_model=MasterAdminResponse,
)
def update_master_admin_endpoint(
    user_id: UUID,
    data: MasterAdminUpdate,
    db: Session = Depends(get_database),
    _: User = Depends(require_role("SUPER ADMIN")),
):
    try:
        return update_master_admin(
            db,
            user_id,
            data,
        )

    except UserServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )


# ============================================================
# DELETE MASTER ADMIN
# SOFT DELETE
# SUPER ADMIN ONLY
# ============================================================

@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_master_admin_endpoint(
    user_id: UUID,
    db: Session = Depends(get_database),
    _: User = Depends(require_role("SUPER ADMIN")),
):
    try:
        delete_master_admin(
            db,
            user_id,
        )

    except UserServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )

    return None