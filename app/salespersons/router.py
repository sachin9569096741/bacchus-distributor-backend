from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_database
from app.permissions.dependencies import require_permission
from app.salespersons.schemas import (
    SalespersonCreate,
    SalespersonResponse,
    SalespersonStatusUpdate,
    SalespersonUpdate,
)
from app.salespersons.repository import (
    get_salesperson_by_user_id,
)
from app.salespersons.service import (
    SalespersonServiceError,
    create_salesperson,
    get_salesperson,
    list_salespersons,
    update_salesperson,
    update_salesperson_status,
)
from app.users.models import User


router = APIRouter(
    prefix="/salespersons",
    tags=["Salespersons"],
)


# ============================================================
# CREATE SALESPERSON
# ============================================================

@router.post(
    "",
    response_model=SalespersonResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_salesperson_endpoint(
    data: SalespersonCreate,
    db: Session = Depends(get_database),
    current_user: User = Depends(
        require_permission("salesperson.create")
    ),
):
    try:
        return create_salesperson(
            db=db,
            data=data,
            current_user=current_user,
        )

    except SalespersonServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


# ============================================================
# LIST SALESPERSONS
# ============================================================

@router.get(
    "",
    response_model=list[SalespersonResponse],
)
def list_salespersons_endpoint(
    db: Session = Depends(get_database),
    current_user: User = Depends(
        require_permission("salesperson.view")
    ),
):
    try:
        return list_salespersons(
            db=db,
            current_user=current_user,
        )

    except SalespersonServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc


# ============================================================
# GET SALESPERSON
# ============================================================

# ============================================================
# GET CURRENT SALESPERSON
# ============================================================

@router.get(
    "/me",
    response_model=SalespersonResponse,
)
def get_current_salesperson_endpoint(
    db: Session = Depends(get_database),
    current_user: User = Depends(
        require_permission("salesperson.view")
    ),
):
    salesperson = get_salesperson_by_user_id(
        db,
        current_user.id,
    )

    if salesperson is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Salesperson profile not found",
        )

    return salesperson

@router.get(
    "/{salesperson_id}",
    response_model=SalespersonResponse,
)
def get_salesperson_endpoint(
    salesperson_id: UUID,
    db: Session = Depends(get_database),
    current_user: User = Depends(
        require_permission("salesperson.view")
    ),
):
    try:
        return get_salesperson(
            db=db,
            salesperson_id=salesperson_id,
            current_user=current_user,
        )

    except SalespersonServiceError as exc:
        message = str(exc)

        if message == "Salesperson not found":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=message,
            ) from exc

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=message,
        ) from exc


# ============================================================
# UPDATE SALESPERSON
# ============================================================

@router.patch(
    "/{salesperson_id}",
    response_model=SalespersonResponse,
)
def update_salesperson_endpoint(
    salesperson_id: UUID,
    data: SalespersonUpdate,
    db: Session = Depends(get_database),
    current_user: User = Depends(
        require_permission("salesperson.update")
    ),
):
    try:
        return update_salesperson(
            db=db,
            salesperson_id=salesperson_id,
            data=data,
            current_user=current_user,
        )

    except SalespersonServiceError as exc:
        message = str(exc)

        if message == "Salesperson not found":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=message,
            ) from exc

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message,
        ) from exc


# ============================================================
# UPDATE SALESPERSON STATUS
# ============================================================

@router.patch(
    "/{salesperson_id}/status",
    response_model=SalespersonResponse,
)
def update_salesperson_status_endpoint(
    salesperson_id: UUID,
    data: SalespersonStatusUpdate,
    db: Session = Depends(get_database),
    current_user: User = Depends(
        require_permission("salesperson.update")
    ),
):
    try:
        return update_salesperson_status(
            db=db,
            salesperson_id=salesperson_id,
            is_active=data.is_active,
            current_user=current_user,
        )

    except SalespersonServiceError as exc:
        message = str(exc)

        if message == "Salesperson not found":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=message,
            ) from exc

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message,
        ) from exc