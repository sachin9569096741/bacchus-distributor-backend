from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.dues.schemas import DueEntryResponse, DueSummaryResponse
from app.dues.service import (
    DueNotFoundError,
    DueService,
    DueServiceError,
)
from app.permissions.dependencies import require_permission
from app.distributors.repository import get_distributor_by_user_id
from app.salespersons.repository import get_salesperson_by_user_id
from app.sellers.repository import get_seller_by_id
from app.users.models import User

router = APIRouter(
    prefix="/dues",
    tags=["Dues"],
)


# ============================================================
# SELLER DUE LEDGER
# ============================================================

@router.get(
    "/seller/{seller_id}",
    response_model=list[DueEntryResponse],
)
def get_seller_due_ledger(
    seller_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_permission("due.view")
    ),
):
    seller = get_seller_by_id(db, seller_id)

    if not seller:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Seller not found.",
        )

    # Distributor scope
    if current_user.role.name == "DISTRIBUTOR":
        distributor = get_distributor_by_user_id(
            db,
            current_user.id,
        )

        if not distributor:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Distributor scope not available.",
            )

        if seller.distributor_id != distributor.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied.",
            )

    # Salesperson scope
    elif current_user.role.name == "SALESPERSON":
        salesperson = get_salesperson_by_user_id(
            db,
            current_user.id,
        )

        if not salesperson:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Salesperson scope not available.",
            )

        if seller.salesperson_id != salesperson.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied.",
            )

    return DueService.list_seller_dues(
        db,
        seller_id,
    )


# ============================================================
# SELLER DUE SUMMARY
# ============================================================

@router.get(
    "/seller/{seller_id}/summary",
    response_model=DueSummaryResponse,
)
def get_seller_due_summary(
    seller_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_permission("due.view")
    ),
):
    seller = get_seller_by_id(db, seller_id)

    if not seller:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Seller not found.",
        )

    # Distributor scope
    if current_user.role.name == "DISTRIBUTOR":
        distributor = get_distributor_by_user_id(
            db,
            current_user.id,
        )

        if (
            not distributor
            or seller.distributor_id != distributor.id
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied.",
            )

    # Salesperson scope
    elif current_user.role.name == "SALESPERSON":
        salesperson = get_salesperson_by_user_id(
            db,
            current_user.id,
        )

        if (
            not salesperson
            or seller.salesperson_id != salesperson.id
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied.",
            )

    return DueService.get_seller_summary(
        db,
        seller_id,
    )


# ============================================================
# SELLER OUTSTANDING
# ============================================================

@router.get(
    "/seller/{seller_id}/outstanding",
)
def get_seller_outstanding(
    seller_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_permission("due.view")
    ),
):
    seller = get_seller_by_id(db, seller_id)

    if not seller:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Seller not found.",
        )

    # Distributor scope
    if current_user.role.name == "DISTRIBUTOR":
        distributor = get_distributor_by_user_id(
            db,
            current_user.id,
        )

        if (
            not distributor
            or seller.distributor_id != distributor.id
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied.",
            )

    # Salesperson scope
    elif current_user.role.name == "SALESPERSON":
        salesperson = get_salesperson_by_user_id(
            db,
            current_user.id,
        )

        if (
            not salesperson
            or seller.salesperson_id != salesperson.id
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied.",
            )

    outstanding = DueService.get_seller_outstanding(
        db,
        seller_id,
    )

    return {
        "seller_id": seller_id,
        "outstanding": outstanding,
    }


# ============================================================
# DISTRIBUTOR DUE LEDGER
# ============================================================

@router.get(
    "/distributor",
    response_model=list[DueEntryResponse],
)
def get_distributor_due_ledger(
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_permission("due.view")
    ),
):
    # Distributor can only see own records
    if current_user.role.name == "DISTRIBUTOR":
        distributor = get_distributor_by_user_id(
            db,
            current_user.id,
        )

        if not distributor:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Distributor scope not available.",
            )

        return DueService.list_distributor_dues(
            db,
            distributor.id,
        )

    # Admin sees organization-wide due ledger
    if current_user.role.name in {
        "SUPER ADMIN",
        "MASTER ADMIN",
    }:
        from app.dues.repository import (
            get_all_due_entries,
        )

        return get_all_due_entries(db)

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Access denied.",
    )