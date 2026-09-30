from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.permissions.dependencies import require_permission
from app.sales.schemas import (
    SaleCreate,
    SaleResponse,
)
from app.sales.service import (
    InvalidSaleError,
    SaleInventoryError,
    SaleNotFoundError,
    SaleScopeError,
    SaleService,
    SaleServiceError,
)
from app.users.models import User


router = APIRouter(
    prefix="/sales",
    tags=["Sales"],
)


# ============================================================
# ERROR HANDLER
# ============================================================

def _handle_sale_error(
    exc: SaleServiceError,
) -> None:

    if isinstance(exc, SaleNotFoundError):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )

    if isinstance(exc, SaleInventoryError):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        )

    if isinstance(exc, SaleScopeError):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        )

    if isinstance(exc, InvalidSaleError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=str(exc),
    )


# ============================================================
# CREATE SALE
# SALESPERSON
# ============================================================

@router.post(
    "",
    response_model=SaleResponse,
    status_code=status.HTTP_201_CREATED,
)
# ============================================================
# CREATE SALE
# SALESPERSON / MASTER ADMIN / SUPER ADMIN
# ============================================================

@router.post(
    "",
    response_model=SaleResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_sale(
    payload: SaleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: User = Depends(
        require_permission("sale.create")
    ),
):
    """
    Create a sale.

    SALESPERSON:
        distributor_id and salesperson_id are derived
        from the authenticated salesperson.

    MASTER ADMIN / SUPER ADMIN:
        distributor_id and salesperson_id are supplied
        by the frontend.

    All seller/distributor/salesperson relationships
    are validated by SaleService.
    """

    role = current_user.role.name

    # ========================================================
    # SALESPERSON
    # ========================================================

    if role == "SALESPERSON":

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

        distributor_id = salesperson.distributor_id
        salesperson_id = salesperson.id

    # ========================================================
    # MASTER ADMIN / SUPER ADMIN
    # ========================================================

    elif role in {"MASTER ADMIN", "SUPER ADMIN"}:

        if payload.distributor_id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Distributor is required.",
            )

        if payload.salesperson_id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Salesperson is required.",
            )

        distributor_id = payload.distributor_id
        salesperson_id = payload.salesperson_id

    # ========================================================
    # OTHER ROLES
    # ========================================================

    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to create a sale.",
        )

    try:

        sale = SaleService.create_sale(
            db=db,
            seller_id=payload.seller_id,
            salesperson_id=salesperson_id,
            distributor_id=distributor_id,
            sale_date=payload.sale_date,
            items=[
                {
                    "product_id": item.product_id,
                    "variant_id": item.variant_id,
                    "quantity": item.quantity,
                    "selling_price": item.selling_price,
                }
                for item in payload.items
            ],
            created_by=current_user.id,
            remarks=payload.remarks,
        )

        db.commit()
        db.refresh(sale)

        return sale

    except SaleServiceError as exc:
        db.rollback()
        _handle_sale_error(exc)


# ============================================================
# MY SALES
# SALESPERSON
# ============================================================

@router.get(
    "/my",
    response_model=list[SaleResponse],
)
def list_my_sales(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: User = Depends(
        require_permission("sale.view")
    ),
):
    """
    Get sales created under the authenticated salesperson.
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

    return SaleService.list_salesperson_sales(
        db=db,
        salesperson_id=salesperson.id,
    )


# ============================================================
# DISTRIBUTOR SALES
# ============================================================

@router.get(
    "/distributor",
    response_model=list[SaleResponse],
)
def list_distributor_sales(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: User = Depends(
        require_permission("sale.view")
    ),
):
    """
    Get sales belonging to the authenticated distributor.
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

    return SaleService.list_distributor_sales(
        db=db,
        distributor_id=distributor.id,
    )


# ============================================================
# SELLER SALES
# ============================================================

@router.get(
    "/seller/{seller_id}",
    response_model=list[SaleResponse],
)
def list_seller_sales(
    seller_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: User = Depends(
        require_permission("sale.view")
    ),
):
    """
    Get sales for a seller.

    Scope is checked against the authenticated user.
    """

    role = current_user.role.name

    try:

        if role in {"SUPER ADMIN", "MASTER ADMIN"}:

            return SaleService.list_seller_sales(
                db=db,
                seller_id=seller_id,
            )

        if role == "DISTRIBUTOR":

            from app.distributors.repository import (
                get_distributor_by_user_id,
            )

            from app.sellers.repository import (
                get_seller_by_id,
            )

            distributor = get_distributor_by_user_id(
                db=db,
                user_id=current_user.id,
            )

            seller = get_seller_by_id(
                db=db,
                seller_id=seller_id,
            )

            if distributor is None:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Distributor profile not found.",
                )

            if (
                seller is None
                or seller.distributor_id != distributor.id
            ):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You cannot access this seller's sales.",
                )

            return SaleService.list_seller_sales(
                db=db,
                seller_id=seller_id,
            )

        if role == "SALESPERSON":

            from app.salespersons.repository import (
                get_salesperson_by_user_id,
            )

            from app.sellers.repository import (
                get_seller_by_id,
            )

            salesperson = get_salesperson_by_user_id(
                db=db,
                user_id=current_user.id,
            )

            seller = get_seller_by_id(
                db=db,
                seller_id=seller_id,
            )

            if salesperson is None:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Salesperson profile not found.",
                )

            if (
                seller is None
                or seller.salesperson_id != salesperson.id
            ):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You cannot access this seller's sales.",
                )

            return SaleService.list_seller_sales(
                db=db,
                seller_id=seller_id,
            )

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient sales access.",
        )

    except SaleServiceError as exc:
        _handle_sale_error(exc)


# ============================================================
# SINGLE SALE
# ============================================================

@router.get(
    "/{sale_id}",
    response_model=SaleResponse,
)
def get_sale(
    sale_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: User = Depends(
        require_permission("sale.view")
    ),
):
    """
    Get a single sale with its items.

    Access is restricted according to the authenticated
    user's distributor/salesperson scope.
    """

    try:

        sale = SaleService.get_sale(
            db=db,
            sale_id=sale_id,
        )

        role = current_user.role.name

        # ----------------------------------------------------
        # ADMIN
        # ----------------------------------------------------

        if role in {"SUPER ADMIN", "MASTER ADMIN"}:
            return sale

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
                or sale.distributor_id != distributor.id
            ):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You cannot access this sale.",
                )

            return sale

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
                or sale.salesperson_id != salesperson.id
            ):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You cannot access this sale.",
                )

            return sale

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient sales access.",
        )

    except SaleServiceError as exc:
        _handle_sale_error(exc)