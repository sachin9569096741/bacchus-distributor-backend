from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.analytics.schemas import (
    AdminAnalyticsResponse,
    DistributorAnalyticsResponse,
    SellerAnalyticsResponse,
)
from app.analytics.service import AnalyticsService
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.distributors.repository import (
    get_distributor_by_user_id,
)
from app.permissions.dependencies import require_permission
from app.salespersons.repository import (
    get_salesperson_by_user_id,
)
from app.sellers.repository import get_seller_by_id
from app.users.models import User


router = APIRouter(
    prefix="/analytics",
    tags=["Analytics"],
)


# ============================================================
# ADMIN ANALYTICS
# ============================================================

@router.get(
    "/admin",
    response_model=AdminAnalyticsResponse,
    dependencies=[
        Depends(require_permission("report.view"))
    ],
)
def get_admin_analytics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role.name not in {
        "SUPER ADMIN",
        "MASTER ADMIN",
    }:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin analytics access required",
        )

    return AnalyticsService.get_admin_analytics(db)


# ============================================================
# DISTRIBUTOR ANALYTICS
# ============================================================

@router.get(
    "/distributor",
    response_model=DistributorAnalyticsResponse,
    dependencies=[
        Depends(require_permission("report.view"))
    ],
)
def get_distributor_analytics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    if current_user.role.name != "DISTRIBUTOR":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Distributor analytics access required",
        )

    distributor = get_distributor_by_user_id(
        db,
        current_user.id,
    )

    if distributor is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Distributor profile not found",
        )

    return AnalyticsService.get_distributor_analytics(
        db,
        distributor.id,
    )


# ============================================================
# SELLER ANALYTICS
# ============================================================

@router.get(
    "/seller/{seller_id}",
    response_model=SellerAnalyticsResponse,
    dependencies=[
        Depends(require_permission("report.view"))
    ],
)
def get_seller_analytics(
    seller_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    seller = get_seller_by_id(
        db,
        seller_id,
    )

    if seller is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Seller not found",
        )

    role_name = current_user.role.name

    # --------------------------------------------------------
    # ADMIN
    # --------------------------------------------------------

    if role_name in {
        "SUPER ADMIN",
        "MASTER ADMIN",
    }:
        return AnalyticsService.get_seller_analytics(
            db,
            seller.id,
        )

    # --------------------------------------------------------
    # DISTRIBUTOR
    # --------------------------------------------------------

    if role_name == "DISTRIBUTOR":

        distributor = get_distributor_by_user_id(
            db,
            current_user.id,
        )

        if distributor is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Distributor profile not found",
            )

        if seller.distributor_id != distributor.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Seller is outside your distributor scope",
            )

        return AnalyticsService.get_seller_analytics(
            db,
            seller.id,
        )

    # --------------------------------------------------------
    # SALESPERSON
    # --------------------------------------------------------

    if role_name == "SALESPERSON":

        salesperson = get_salesperson_by_user_id(
            db,
            current_user.id,
        )

        if salesperson is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Salesperson profile not found",
            )

        if seller.salesperson_id != salesperson.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Seller is outside your salesperson scope",
            )

        return AnalyticsService.get_seller_analytics(
            db,
            seller.id,
        )

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="You do not have seller analytics access",
    )