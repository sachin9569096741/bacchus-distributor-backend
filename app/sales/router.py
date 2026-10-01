from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
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
# HELPERS
# ============================================================

ADMIN_ROLES = {
    "SUPER ADMIN",
    "MASTER ADMIN",
}


def handle_sale_error(
    exc: SaleServiceError,
) -> None:

    if isinstance(
        exc,
        SaleNotFoundError,
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )

    if isinstance(
        exc,
        SaleInventoryError,
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        )

    if isinstance(
        exc,
        SaleScopeError,
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        )

    if isinstance(
        exc,
        InvalidSaleError,
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=str(exc),
    )


def get_salesperson_for_user(
    db: Session,
    user_id: UUID,
):
    from app.salespersons.repository import (
        get_salesperson_by_user_id,
    )

    salesperson = get_salesperson_by_user_id(
        db=db,
        user_id=user_id,
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

    return salesperson


def get_distributor_for_user(
    db: Session,
    user_id: UUID,
):
    from app.distributors.repository import (
        get_distributor_by_user_id,
    )

    distributor = get_distributor_by_user_id(
        db=db,
        user_id=user_id,
    )

    if distributor is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Distributor profile not found.",
        )

    if not distributor.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Distributor account is inactive.",
        )

    return distributor


# ============================================================
# CREATE SALE
# ============================================================

@router.post(
    "",
    response_model=SaleResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_sale(
    payload: SaleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_user
    ),
    _: User = Depends(
        require_permission("sale.create")
    ),
):
    """
    Create a sale.

    SALESPERSON:
        Distributor and salesperson are derived
        from authenticated user.

    DISTRIBUTOR:
        Distributor is derived from authenticated
        distributor account. Salesperson must belong
        to that distributor.

    MASTER ADMIN / SUPER ADMIN:
        Distributor and salesperson can be selected
        explicitly, but relationships are validated
        server-side.
    """

    role = current_user.role.name

    try:

        # ====================================================
        # SALESPERSON
        # ====================================================

        if role == "SALESPERSON":

            salesperson = (
                get_salesperson_for_user(
                    db=db,
                    user_id=current_user.id,
                )
            )

            sale = SaleService.create_sale(
                db=db,
                seller_id=payload.seller_id,
                salesperson_id=salesperson.id,
                distributor_id=(
                    salesperson.distributor_id
                ),
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

        # ====================================================
        # DISTRIBUTOR
        # ====================================================

        if role == "DISTRIBUTOR":

            distributor = (
                get_distributor_for_user(
                    db=db,
                    user_id=current_user.id,
                )
            )

            if not payload.salesperson_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=(
                        "salesperson_id is required "
                        "when a distributor creates a sale."
                    ),
                )

            salesperson = (
                SaleService._get_salesperson(
                    db=db,
                    salesperson_id=payload.salesperson_id,
                )
            )

            if salesperson.distributor_id != distributor.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=(
                        "Salesperson does not belong "
                        "to your distributor."
                    ),
                )

            sale = SaleService.create_sale(
                db=db,
                seller_id=payload.seller_id,
                salesperson_id=salesperson.id,
                distributor_id=distributor.id,
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

        # ====================================================
        # MASTER ADMIN / SUPER ADMIN
        # ====================================================

        if role in ADMIN_ROLES:

            if not payload.distributor_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="distributor_id is required.",
                )

            if not payload.salesperson_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="salesperson_id is required.",
                )

            distributor = (
                SaleService._get_distributor(
                    db=db,
                    distributor_id=(
                        payload.distributor_id
                    ),
                )
            )

            salesperson = (
                SaleService._get_salesperson(
                    db=db,
                    salesperson_id=(
                        payload.salesperson_id
                    ),
                )
            )

            if (
                salesperson.distributor_id
                != distributor.id
            ):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=(
                        "Salesperson does not belong "
                        "to the selected distributor."
                    ),
                )

            sale = SaleService.create_sale(
                db=db,
                seller_id=payload.seller_id,
                salesperson_id=salesperson.id,
                distributor_id=distributor.id,
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

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to create sales.",
        )

    except SaleServiceError as exc:

        db.rollback()

        handle_sale_error(exc)


# ============================================================
# ALL SALES
# MASTER ADMIN / SUPER ADMIN
# ============================================================

@router.get(
    "",
    response_model=list[SaleResponse],
)
def list_all_sales(
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_user
    ),
    _: User = Depends(
        require_permission("sale.view")
    ),
):
    """
    Organization-wide sales.

    Only Master Admin / Super Admin.
    """

    if current_user.role.name not in ADMIN_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can access all sales.",
        )

    return (
        db.query(
            __import__(
                "app.sales.models",
                fromlist=["Sale"],
            ).Sale
        )
        .order_by(
            __import__(
                "app.sales.models",
                fromlist=["Sale"],
            ).Sale.created_at.desc()
        )
        .all()
    )


# ============================================================
# MY SALES
# ============================================================

@router.get(
    "/my",
    response_model=list[SaleResponse],
)
def list_my_sales(
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_user
    ),
    _: User = Depends(
        require_permission("sale.view")
    ),
):
    if current_user.role.name != "SALESPERSON":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This endpoint is for salespersons.",
        )

    salesperson = get_salesperson_for_user(
        db=db,
        user_id=current_user.id,
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
    current_user: User = Depends(
        get_current_user
    ),
    _: User = Depends(
        require_permission("sale.view")
    ),
):
    if current_user.role.name != "DISTRIBUTOR":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This endpoint is for distributors.",
        )

    distributor = get_distributor_for_user(
        db=db,
        user_id=current_user.id,
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
    current_user: User = Depends(
        get_current_user
    ),
    _: User = Depends(
        require_permission("sale.view")
    ),
):

    role = current_user.role.name

    try:

        # ADMIN
        if role in ADMIN_ROLES:

            return SaleService.list_seller_sales(
                db=db,
                seller_id=seller_id,
            )

        # DISTRIBUTOR
        if role == "DISTRIBUTOR":

            distributor = (
                get_distributor_for_user(
                    db=db,
                    user_id=current_user.id,
                )
            )

            from app.sellers.repository import (
                get_seller_by_id,
            )

            seller = get_seller_by_id(
                db=db,
                seller_id=seller_id,
            )

            if (
                seller is None
                or seller.distributor_id
                != distributor.id
            ):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=(
                        "You cannot access "
                        "this seller's sales."
                    ),
                )

            return SaleService.list_seller_sales(
                db=db,
                seller_id=seller_id,
            )

        # SALESPERSON
        if role == "SALESPERSON":

            salesperson = (
                get_salesperson_for_user(
                    db=db,
                    user_id=current_user.id,
                )
            )

            from app.sellers.repository import (
                get_seller_by_id,
            )

            seller = get_seller_by_id(
                db=db,
                seller_id=seller_id,
            )

            if (
                seller is None
                or seller.salesperson_id
                != salesperson.id
            ):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=(
                        "You cannot access "
                        "this seller's sales."
                    ),
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
        handle_sale_error(exc)


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
    current_user: User = Depends(
        get_current_user
    ),
    _: User = Depends(
        require_permission("sale.view")
    ),
):

    try:

        sale = SaleService.get_sale(
            db=db,
            sale_id=sale_id,
        )

        role = current_user.role.name

        # ADMIN
        if role in ADMIN_ROLES:
            return sale

        # DISTRIBUTOR
        if role == "DISTRIBUTOR":

            distributor = (
                get_distributor_for_user(
                    db=db,
                    user_id=current_user.id,
                )
            )

            if (
                sale.distributor_id
                != distributor.id
            ):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You cannot access this sale.",
                )

            return sale

        # SALESPERSON
        if role == "SALESPERSON":

            salesperson = (
                get_salesperson_for_user(
                    db=db,
                    user_id=current_user.id,
                )
            )

            if (
                sale.salesperson_id
                != salesperson.id
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
        handle_sale_error(exc)