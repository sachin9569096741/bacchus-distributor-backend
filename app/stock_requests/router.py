from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.permissions.dependencies import require_permission
from app.stock_requests.models import StockRequestStatus
from app.stock_requests.schemas import (
    StockRequestCreate,
    StockRequestReject,
    StockRequestResponse,
)
from app.stock_requests.service import (
    InvalidStockRequestError,
    StockRequestAlreadyProcessedError,
    StockRequestInventoryError,
    StockRequestNotFoundError,
    StockRequestService,
    StockRequestServiceError,
)
from app.users.models import User


router = APIRouter(
    prefix="/stock-requests",
    tags=["Stock Requests"],
)


# ============================================================
# HELPERS
# ============================================================

def _handle_stock_request_error(
    exc: StockRequestServiceError,
) -> None:

    if isinstance(exc, StockRequestNotFoundError):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )

    if isinstance(exc, StockRequestAlreadyProcessedError):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        )

    if isinstance(exc, StockRequestInventoryError):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        )

    if isinstance(exc, InvalidStockRequestError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=str(exc),
    )


# ============================================================
# CREATE STOCK REQUEST
# SALESPERSON ONLY
# ============================================================

@router.post(
    "",
    response_model=StockRequestResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_stock_request(
    payload: StockRequestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: User = Depends(
        require_permission("stock_request.create")
    ),
):
    """
    Create a stock request for the authenticated salesperson.

    distributor_id and salesperson_id are derived from the
    authenticated salesperson account.
    """

    if current_user.role.name != "SALESPERSON":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only a salesperson can create a stock request.",
        )

    try:

        from app.salespersons.repository import (
            get_salesperson_by_user_id,
        )

        salesperson = get_salesperson_by_user_id(
            db=db,
            user_id=current_user.id,
        )

        if salesperson is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Salesperson profile not found.",
            )

        if not salesperson.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Salesperson account is inactive.",
            )

        stock_request = StockRequestService.create_request(
            db=db,
            salesperson_id=salesperson.id,
            distributor_id=salesperson.distributor_id,
            items=[
                {
                    "product_id": item.product_id,
                    "variant_id": item.variant_id,
                    "quantity": item.quantity,
                }
                for item in payload.items
            ],
            remarks=payload.remarks,
        )

        db.commit()
        db.refresh(stock_request)

        return stock_request

    except StockRequestServiceError as exc:
        db.rollback()
        _handle_stock_request_error(exc)


# ============================================================
# LIST MY REQUESTS
# SALESPERSON
# ============================================================

@router.get(
    "/my",
    response_model=list[StockRequestResponse],
)
def list_my_stock_requests(
    request_status: StockRequestStatus | None = Query(
        default=None,
        alias="status",
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: User = Depends(
        require_permission("stock_request.view")
    ),
):
    """
    Get stock requests belonging to the authenticated
    salesperson.
    """

    if current_user.role.name != "SALESPERSON":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This endpoint is for salespersons.",
        )

    from app.salespersons.repository import (
        get_salesperson_by_user_id,
    )

    salesperson = get_salesperson_by_user_id(
        db=db,
        user_id=current_user.id,
    )

    if salesperson is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Salesperson profile not found.",
        )

    return StockRequestService.list_salesperson_requests(
        db=db,
        salesperson_id=salesperson.id,
        status=request_status,
    )


# ============================================================
# DISTRIBUTOR REQUESTS
# ============================================================

@router.get(
    "/distributor",
    response_model=list[StockRequestResponse],
)
def list_distributor_stock_requests(
    request_status: StockRequestStatus | None = Query(
        default=None,
        alias="status",
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: User = Depends(
        require_permission("stock_request.view")
    ),
):
    """
    Get stock requests for the authenticated distributor.
    """

    if current_user.role.name != "DISTRIBUTOR":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This endpoint is for distributors.",
        )

    from app.distributors.repository import (
        get_distributor_by_user_id,
    )

    distributor = get_distributor_by_user_id(
        db=db,
        user_id=current_user.id,
    )

    if distributor is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Distributor profile not found.",
        )

    return StockRequestService.list_distributor_requests(
        db=db,
        distributor_id=distributor.id,
        status=request_status,
    )


# ============================================================
# DISTRIBUTOR PENDING REQUESTS
# ============================================================

@router.get(
    "/distributor/pending",
    response_model=list[StockRequestResponse],
)
def list_pending_stock_requests(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: User = Depends(
        require_permission("stock_request.view")
    ),
):
    """
    Get pending stock requests for the authenticated
    distributor.
    """

    if current_user.role.name != "DISTRIBUTOR":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This endpoint is for distributors.",
        )

    from app.distributors.repository import (
        get_distributor_by_user_id,
    )

    distributor = get_distributor_by_user_id(
        db=db,
        user_id=current_user.id,
    )

    if distributor is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Distributor profile not found.",
        )

    return StockRequestService.list_pending_requests(
        db=db,
        distributor_id=distributor.id,
    )


# ============================================================
# GET SINGLE REQUEST
# ============================================================

@router.get(
    "/{stock_request_id}",
    response_model=StockRequestResponse,
)
def get_stock_request(
    stock_request_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: User = Depends(
        require_permission("stock_request.view")
    ),
):
    """
    Get one stock request.

    Access is checked against the authenticated user's
    distributor/salesperson scope.
    """

    try:

        stock_request = StockRequestService.get_request(
            db=db,
            stock_request_id=stock_request_id,
        )

        role = current_user.role.name

        # ----------------------------------------------------
        # ADMIN
        # ----------------------------------------------------

        if role in {"SUPER ADMIN", "MASTER ADMIN"}:
            return stock_request

        # ----------------------------------------------------
        # DISTRIBUTOR
        # ----------------------------------------------------

        if role == "DISTRIBUTOR":

            from app.distributors.repository import (
                get_distributor_by_user_id,
            )

            distributor = get_distributor_by_user_id(
                db=db,
                user_id=current_user.id,
            )

            if (
                distributor is None
                or stock_request.distributor_id != distributor.id
            ):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You cannot access this stock request.",
                )

            return stock_request

        # ----------------------------------------------------
        # SALESPERSON
        # ----------------------------------------------------

        if role == "SALESPERSON":

            from app.salespersons.repository import (
                get_salesperson_by_user_id,
            )

            salesperson = get_salesperson_by_user_id(
                db=db,
                user_id=current_user.id,
            )

            if (
                salesperson is None
                or stock_request.salesperson_id != salesperson.id
            ):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You cannot access this stock request.",
                )

            return stock_request

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient stock-request access.",
        )

    except StockRequestServiceError as exc:
        _handle_stock_request_error(exc)


# ============================================================
# APPROVE REQUEST
# DISTRIBUTOR
# ============================================================

@router.post(
    "/{stock_request_id}/approve",
    response_model=StockRequestResponse,
)
def approve_stock_request(
    stock_request_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: User = Depends(
        require_permission("stock_request.approve")
    ),
):
    """
    Approve a pending stock request.

    Approval transfers stock:

        Distributor stock  - quantity
        Salesperson stock  + quantity
    """

    if current_user.role.name not in {
        "DISTRIBUTOR",
        "MASTER ADMIN",
        "SUPER ADMIN",
    }:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You cannot approve stock requests.",
        )

    try:

        # ----------------------------------------------------
        # Get distributor scope
        # ----------------------------------------------------

        if current_user.role.name == "DISTRIBUTOR":

            from app.distributors.repository import (
                get_distributor_by_user_id,
            )

            distributor = get_distributor_by_user_id(
                db=db,
                user_id=current_user.id,
            )

            if distributor is None:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Distributor profile not found.",
                )

            stock_request = (
                StockRequestService.get_request(
                    db=db,
                    stock_request_id=stock_request_id,
                )
            )

            if (
                stock_request.distributor_id
                != distributor.id
            ):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You cannot approve this stock request.",
                )

        else:
            stock_request = (
                StockRequestService.get_request(
                    db=db,
                    stock_request_id=stock_request_id,
                )
            )

        # ----------------------------------------------------
        # Approve
        # ----------------------------------------------------

        stock_request = StockRequestService.approve_request(
            db=db,
            stock_request_id=stock_request_id,
            reviewed_by=current_user.id,
        )

        db.commit()
        db.refresh(stock_request)

        return stock_request

    except StockRequestServiceError as exc:
        db.rollback()
        _handle_stock_request_error(exc)


# ============================================================
# REJECT REQUEST
# DISTRIBUTOR
# ============================================================

@router.post(
    "/{stock_request_id}/reject",
    response_model=StockRequestResponse,
)
def reject_stock_request(
    stock_request_id: UUID,
    payload: StockRequestReject,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: User = Depends(
        require_permission("stock_request.reject")
    ),
):
    """
    Reject a pending stock request.
    """

    if current_user.role.name not in {
        "DISTRIBUTOR",
        "MASTER ADMIN",
        "SUPER ADMIN",
    }:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You cannot reject stock requests.",
        )

    try:

        # ----------------------------------------------------
        # Distributor scope
        # ----------------------------------------------------

        stock_request = (
            StockRequestService.get_request(
                db=db,
                stock_request_id=stock_request_id,
            )
        )

        if current_user.role.name == "DISTRIBUTOR":

            from app.distributors.repository import (
                get_distributor_by_user_id,
            )

            distributor = get_distributor_by_user_id(
                db=db,
                user_id=current_user.id,
            )

            if distributor is None:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Distributor profile not found.",
                )

            if (
                stock_request.distributor_id
                != distributor.id
            ):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You cannot reject this stock request.",
                )

        # ----------------------------------------------------
        # Reject
        # ----------------------------------------------------

        stock_request = StockRequestService.reject_request(
            db=db,
            stock_request_id=stock_request_id,
            reviewed_by=current_user.id,
            rejection_reason=payload.rejection_reason,
        )

        db.commit()
        db.refresh(stock_request)

        return stock_request

    except StockRequestServiceError as exc:
        db.rollback()
        _handle_stock_request_error(exc)