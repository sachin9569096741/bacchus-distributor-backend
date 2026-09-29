from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.distributors.repository import get_distributor_by_user_id
from app.permissions.dependencies import require_permission
from app.reports.schemas import (
    DueReportItem,
    InventoryReportItem,
    PaymentProofReportItem,
    SalesReportItem,
    StockRequestReportItem,
)
from app.reports.service import ReportService
from app.salespersons.repository import get_salesperson_by_user_id
from app.sellers.repository import get_seller_by_id
from app.users.models import User


router = APIRouter(
    prefix="/reports",
    tags=["Reports"],
)


ADMIN_ROLES = {
    "SUPER ADMIN",
    "MASTER ADMIN",
}


def _validate_dates(
    from_date: date | None,
    to_date: date | None,
) -> None:
    if from_date and to_date and from_date > to_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="from_date cannot be greater than to_date",
        )


# ============================================================
# SALES REPORT
# ============================================================

@router.get(
    "/sales",
    response_model=list[SalesReportItem],
    dependencies=[
        Depends(require_permission("report.view"))
    ],
)
def get_sales_report(
    from_date: date | None = Query(default=None),
    to_date: date | None = Query(default=None),
    seller_id: UUID | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _validate_dates(from_date, to_date)

    role = current_user.role.name

    if role in ADMIN_ROLES:
        return ReportService.get_sales_report(
            db,
            seller_id=seller_id,
            from_date=from_date,
            to_date=to_date,
        )

    if role == "DISTRIBUTOR":
        distributor = get_distributor_by_user_id(
            db,
            current_user.id,
        )

        if distributor is None:
            raise HTTPException(
                status_code=404,
                detail="Distributor profile not found",
            )

        if seller_id is not None:
            seller = get_seller_by_id(
                db,
                seller_id,
            )

            if (
                seller is None
                or seller.distributor_id != distributor.id
            ):
                raise HTTPException(
                    status_code=403,
                    detail="Seller is outside your scope",
                )

        return ReportService.get_sales_report(
            db,
            distributor_id=distributor.id,
            seller_id=seller_id,
            from_date=from_date,
            to_date=to_date,
        )

    if role == "SALESPERSON":
        salesperson = get_salesperson_by_user_id(
            db,
            current_user.id,
        )

        if salesperson is None:
            raise HTTPException(
                status_code=404,
                detail="Salesperson profile not found",
            )

        if seller_id is not None:
            seller = get_seller_by_id(
                db,
                seller_id,
            )

            if (
                seller is None
                or seller.salesperson_id != salesperson.id
            ):
                raise HTTPException(
                    status_code=403,
                    detail="Seller is outside your scope",
                )

        return ReportService.get_sales_report(
            db,
            salesperson_id=salesperson.id,
            seller_id=seller_id,
            from_date=from_date,
            to_date=to_date,
        )

    raise HTTPException(
        status_code=403,
        detail="You do not have access to sales reports",
    )


# ============================================================
# INVENTORY REPORT
# ============================================================

@router.get(
    "/inventory",
    response_model=list[InventoryReportItem],
    dependencies=[
        Depends(require_permission("report.view"))
    ],
)
def get_inventory_report(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    role = current_user.role.name

    if role in ADMIN_ROLES:
        return ReportService.get_inventory_report(db)

    if role == "DISTRIBUTOR":
        distributor = get_distributor_by_user_id(
            db,
            current_user.id,
        )

        if distributor is None:
            raise HTTPException(
                status_code=404,
                detail="Distributor profile not found",
            )

        return ReportService.get_inventory_report(
            db,
            distributor_id=distributor.id,
        )

    if role == "SALESPERSON":
        salesperson = get_salesperson_by_user_id(
            db,
            current_user.id,
        )

        if salesperson is None:
            raise HTTPException(
                status_code=404,
                detail="Salesperson profile not found",
            )

        return ReportService.get_inventory_report(
            db,
            distributor_id=salesperson.distributor_id,
            salesperson_id=salesperson.id,
        )

    raise HTTPException(
        status_code=403,
        detail="You do not have access to inventory reports",
    )


# ============================================================
# STOCK REQUEST REPORT
# ============================================================

@router.get(
    "/stock-requests",
    response_model=list[StockRequestReportItem],
    dependencies=[
        Depends(require_permission("report.view"))
    ],
)
def get_stock_request_report(
    from_date: date | None = Query(default=None),
    to_date: date | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _validate_dates(from_date, to_date)

    role = current_user.role.name

    if role in ADMIN_ROLES:
        return ReportService.get_stock_request_report(
            db,
            from_date=from_date,
            to_date=to_date,
        )

    if role == "DISTRIBUTOR":
        distributor = get_distributor_by_user_id(
            db,
            current_user.id,
        )

        if distributor is None:
            raise HTTPException(
                status_code=404,
                detail="Distributor profile not found",
            )

        return ReportService.get_stock_request_report(
            db,
            distributor_id=distributor.id,
            from_date=from_date,
            to_date=to_date,
        )

    if role == "SALESPERSON":
        salesperson = get_salesperson_by_user_id(
            db,
            current_user.id,
        )

        if salesperson is None:
            raise HTTPException(
                status_code=404,
                detail="Salesperson profile not found",
            )

        return ReportService.get_stock_request_report(
            db,
            salesperson_id=salesperson.id,
            from_date=from_date,
            to_date=to_date,
        )

    raise HTTPException(
        status_code=403,
        detail="You do not have access to stock request reports",
    )


# ============================================================
# DUE REPORT
# ============================================================

@router.get(
    "/due",
    response_model=list[DueReportItem],
    dependencies=[
        Depends(require_permission("report.view"))
    ],
)
def get_due_report(
    from_date: date | None = Query(default=None),
    to_date: date | None = Query(default=None),
    seller_id: UUID | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _validate_dates(from_date, to_date)

    role = current_user.role.name

    if role in ADMIN_ROLES:
        return ReportService.get_due_report(
            db,
            seller_id=seller_id,
            from_date=from_date,
            to_date=to_date,
        )

    if role == "DISTRIBUTOR":
        distributor = get_distributor_by_user_id(
            db,
            current_user.id,
        )

        if distributor is None:
            raise HTTPException(
                status_code=404,
                detail="Distributor profile not found",
            )

        if seller_id is not None:
            seller = get_seller_by_id(
                db,
                seller_id,
            )

            if (
                seller is None
                or seller.distributor_id != distributor.id
            ):
                raise HTTPException(
                    status_code=403,
                    detail="Seller is outside your scope",
                )

        return ReportService.get_due_report(
            db,
            distributor_id=distributor.id,
            seller_id=seller_id,
            from_date=from_date,
            to_date=to_date,
        )

    if role == "SALESPERSON":
        salesperson = get_salesperson_by_user_id(
            db,
            current_user.id,
        )

        if salesperson is None:
            raise HTTPException(
                status_code=404,
                detail="Salesperson profile not found",
            )

        if seller_id is not None:
            seller = get_seller_by_id(
                db,
                seller_id,
            )

            if (
                seller is None
                or seller.salesperson_id != salesperson.id
            ):
                raise HTTPException(
                    status_code=403,
                    detail="Seller is outside your scope",
                )

        # DueLedger does not contain salesperson_id,
        # therefore seller scope is resolved explicitly.
        if seller_id is not None:
            return ReportService.get_due_report(
                db,
                seller_id=seller_id,
                from_date=from_date,
                to_date=to_date,
            )

        from app.sellers.repository import (
            get_sellers_by_salesperson,
        )

        sellers = get_sellers_by_salesperson(
            db,
            salesperson.id,
        )

        seller_ids = [seller.id for seller in sellers]

        if not seller_ids:
            return []

        # Query each seller within the salesperson scope.
        results = []

        for scoped_seller_id in seller_ids:
            results.extend(
                ReportService.get_due_report(
                    db,
                    seller_id=scoped_seller_id,
                    from_date=from_date,
                    to_date=to_date,
                )
            )

        return results

    raise HTTPException(
        status_code=403,
        detail="You do not have access to due reports",
    )


# ============================================================
# PAYMENT PROOF REPORT
# ============================================================

@router.get(
    "/payment-proofs",
    response_model=list[PaymentProofReportItem],
    dependencies=[
        Depends(require_permission("report.view"))
    ],
)
def get_payment_proof_report(
    from_date: date | None = Query(default=None),
    to_date: date | None = Query(default=None),
    seller_id: UUID | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _validate_dates(from_date, to_date)

    role = current_user.role.name

    if role in ADMIN_ROLES:
        return ReportService.get_payment_proof_report(
            db,
            seller_id=seller_id,
            from_date=from_date,
            to_date=to_date,
        )

    if role == "DISTRIBUTOR":
        distributor = get_distributor_by_user_id(
            db,
            current_user.id,
        )

        if distributor is None:
            raise HTTPException(
                status_code=404,
                detail="Distributor profile not found",
            )

        if seller_id is not None:
            seller = get_seller_by_id(
                db,
                seller_id,
            )

            if (
                seller is None
                or seller.distributor_id != distributor.id
            ):
                raise HTTPException(
                    status_code=403,
                    detail="Seller is outside your scope",
                )

        return ReportService.get_payment_proof_report(
            db,
            distributor_id=distributor.id,
            seller_id=seller_id,
            from_date=from_date,
            to_date=to_date,
        )

    if role == "SALESPERSON":
        salesperson = get_salesperson_by_user_id(
            db,
            current_user.id,
        )

        if salesperson is None:
            raise HTTPException(
                status_code=404,
                detail="Salesperson profile not found",
            )

        if seller_id is not None:
            seller = get_seller_by_id(
                db,
                seller_id,
            )

            if (
                seller is None
                or seller.salesperson_id != salesperson.id
            ):
                raise HTTPException(
                    status_code=403,
                    detail="Seller is outside your scope",
                )

        return ReportService.get_payment_proof_report(
            db,
            salesperson_id=salesperson.id,
            seller_id=seller_id,
            from_date=from_date,
            to_date=to_date,
        )

    raise HTTPException(
        status_code=403,
        detail="You do not have access to payment proof reports",
    )