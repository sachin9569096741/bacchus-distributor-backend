from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_database
from app.distributors.schemas import (
    DistributorCreate,
    DistributorResponse,
    DistributorStatusUpdate,
    DistributorUpdate,
)
from app.distributors.service import (
    DistributorServiceError,
    create_distributor,
    get_current_distributor,
    get_distributor,
    list_distributors,
    update_distributor,
    update_distributor_status,
)
from app.permissions.dependencies import (
    require_any_role,
    require_permission,
)
from app.users.models import User


router = APIRouter(
    prefix="/distributors",
    tags=["Distributors"],
)


# ============================================================
# CREATE DISTRIBUTOR
# ============================================================

@router.post(
    "",
    response_model=DistributorResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_distributor_endpoint(
    data: DistributorCreate,
    db: Session = Depends(get_database),
    _: User = Depends(
        require_permission("distributor.create")
    ),
):
    try:
        return create_distributor(
            db=db,
            data=data,
        )

    except DistributorServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


# ============================================================
# LIST DISTRIBUTORS
# ============================================================

@router.get(
    "",
    response_model=list[DistributorResponse],
)
def list_distributors_endpoint(
    db: Session = Depends(get_database),
    _: User = Depends(
        require_any_role(
            "SUPER ADMIN",
            "MASTER ADMIN",
        )
    ),
):
    try:
        return list_distributors(db)

    except DistributorServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


# ============================================================
# CURRENT DISTRIBUTOR
# ============================================================

@router.get(
    "/me",
    response_model=DistributorResponse,
)
def get_current_distributor_endpoint(
    db: Session = Depends(get_database),
    current_user: User = Depends(
        require_permission("distributor.view")
    ),
):
    try:
        return get_current_distributor(
            db=db,
            user_id=current_user.id,
        )

    except DistributorServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


# ============================================================
# UPDATE DISTRIBUTOR STATUS
# ============================================================

@router.patch(
    "/{distributor_id}/status",
    response_model=DistributorResponse,
)
def update_distributor_status_endpoint(
    distributor_id: UUID,
    data: DistributorStatusUpdate,
    db: Session = Depends(get_database),
    _: User = Depends(
        require_permission("distributor.update")
    ),
):
    try:
        return update_distributor_status(
            db=db,
            distributor_id=distributor_id,
            is_active=data.is_active,
        )

    except DistributorServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


# ============================================================
# GET DISTRIBUTOR BY ID
# ============================================================

@router.get(
    "/{distributor_id}",
    response_model=DistributorResponse,
)
def get_distributor_endpoint(
    distributor_id: UUID,
    db: Session = Depends(get_database),
    _: User = Depends(
        require_permission("distributor.view")
    ),
):
    try:
        return get_distributor(
            db=db,
            distributor_id=distributor_id,
        )

    except DistributorServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


# ============================================================
# UPDATE DISTRIBUTOR
# ============================================================

@router.patch(
    "/{distributor_id}",
    response_model=DistributorResponse,
)
def update_distributor_endpoint(
    distributor_id: UUID,
    data: DistributorUpdate,
    db: Session = Depends(get_database),
    _: User = Depends(
        require_permission("distributor.update")
    ),
):
    try:
        return update_distributor(
            db=db,
            distributor_id=distributor_id,
            data=data,
        )

    except DistributorServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc