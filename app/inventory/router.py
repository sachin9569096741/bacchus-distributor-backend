from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.inventory.models import InventoryMovementType
from app.inventory.schemas import (
    InventoryLedgerResponse,
    InventoryMovementCreate,
    InventoryResponse,
)
from app.inventory.service import (
    InventoryService,
    InventoryServiceError,
    InsufficientStockError,
    InvalidInventoryMovementError,
    InventoryNotFoundError,
)
from app.permissions.dependencies import require_permission
from app.users.models import User


router = APIRouter(
    prefix="/inventory",
    tags=["Inventory"],
)


# ============================================================
# HELPERS
# ============================================================

def _handle_inventory_error(exc: InventoryServiceError) -> None:
    if isinstance(exc, InventoryNotFoundError):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )

    if isinstance(exc, InsufficientStockError):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        )

    if isinstance(exc, InvalidInventoryMovementError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=str(exc),
    )


# ============================================================
# VIEW INVENTORY
# ============================================================

@router.get(
    "",
    response_model=list[InventoryResponse],
)
def list_inventory(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: User = Depends(require_permission("inventory.view")),
    distributor_id: UUID | None = Query(default=None),
    salesperson_id: UUID | None = Query(default=None),
):
    """
    List inventory.

    Scope:
    - SUPER ADMIN / MASTER ADMIN:
        Can query organizational inventory.
    - DISTRIBUTOR:
        Own distributor inventory only.
    - SALESPERSON:
        Own salesperson inventory only.
    """

    try:
        role = current_user.role.name

        # ----------------------------------------------------
        # ADMIN
        # ----------------------------------------------------

        if role in {"SUPER ADMIN", "MASTER ADMIN"}:

            if distributor_id is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="distributor_id is required for admin inventory queries.",
                )

            if salesperson_id is not None:
                return InventoryService.list_salesperson_inventory(
                    db=db,
                    distributor_id=distributor_id,
                    salesperson_id=salesperson_id,
                )

            return InventoryService.list_distributor_inventory(
                db=db,
                distributor_id=distributor_id,
            )

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

            if distributor is None:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Distributor profile not found.",
                )

            # Frontend cannot change distributor scope.
            if (
                distributor_id is not None
                and distributor_id != distributor.id
            ):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You cannot access another distributor's inventory.",
                )

            if salesperson_id is not None:
                return InventoryService.list_salesperson_inventory(
                    db=db,
                    distributor_id=distributor.id,
                    salesperson_id=salesperson_id,
                )

            return InventoryService.list_distributor_inventory(
                db=db,
                distributor_id=distributor.id,
            )

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

            if salesperson is None:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Salesperson profile not found.",
                )

            # Salesperson can only see own stock.
            if (
                salesperson_id is not None
                and salesperson_id != salesperson.id
            ):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You cannot access another salesperson's inventory.",
                )

            return InventoryService.list_salesperson_inventory(
                db=db,
                distributor_id=salesperson.distributor_id,
                salesperson_id=salesperson.id,
            )

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient inventory access.",
        )

    except InventoryServiceError as exc:
        _handle_inventory_error(exc)


# ============================================================
# GET SINGLE INVENTORY POSITION
# ============================================================

@router.get(
    "/{inventory_id}",
    response_model=InventoryResponse,
)
def get_inventory(
    inventory_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: User = Depends(require_permission("inventory.view")),
):
    """
    Get one inventory position.

    Scope validation is performed before exposing the record.
    """

    try:
        inventory = InventoryService.get_inventory(
            db=db,
            inventory_id=inventory_id,
        )

        role = current_user.role.name

        # ----------------------------------------------------
        # ADMIN
        # ----------------------------------------------------

        if role in {"SUPER ADMIN", "MASTER ADMIN"}:
            return inventory

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
                or inventory.distributor_id != distributor.id
            ):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You cannot access this inventory.",
                )

            return inventory

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
                or inventory.salesperson_id != salesperson.id
            ):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You cannot access this inventory.",
                )

            return inventory

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient inventory access.",
        )

    except InventoryServiceError as exc:
        _handle_inventory_error(exc)

@router.get(
    "/ledger/recent",
    response_model=list[InventoryLedgerResponse],
)
def recent_inventory_ledger(
    distributor_id: UUID | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: User = Depends(require_permission("inventory.view")),
):
    """
    Get recent inventory movements.

    Distributor scope is derived from the authenticated
    distributor account.
    """

    role = current_user.role.name

    # --------------------------------------------------------
    # ADMIN
    # --------------------------------------------------------

    if role in {"SUPER ADMIN", "MASTER ADMIN"}:

        if distributor_id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="distributor_id is required for admin queries.",
            )

        return InventoryService.get_recent_ledger(
            db=db,
            distributor_id=distributor_id,
            limit=limit,
        )

    # --------------------------------------------------------
    # DISTRIBUTOR
    # --------------------------------------------------------

    if role == "DISTRIBUTOR":

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
            distributor_id is not None
            and distributor_id != distributor.id
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You cannot access another distributor's ledger.",
            )

        return InventoryService.get_recent_ledger(
            db=db,
            distributor_id=distributor.id,
            limit=limit,
        )

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Recent distributor ledger is not available for this role.",
    )



# ============================================================
# INVENTORY LEDGER
# ============================================================

@router.get(
    "/{inventory_id}/ledger",
    response_model=list[InventoryLedgerResponse],
)
def get_inventory_ledger(
    inventory_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: User = Depends(require_permission("inventory.view")),
):
    """
    Get complete movement history for an inventory position.
    """

    try:
        inventory = InventoryService.get_inventory(
            db=db,
            inventory_id=inventory_id,
        )

        role = current_user.role.name

        # ----------------------------------------------------
        # ADMIN
        # ----------------------------------------------------

        if role in {"SUPER ADMIN", "MASTER ADMIN"}:
            return InventoryService.get_ledger(
                db=db,
                inventory_id=inventory_id,
            )

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
                or inventory.distributor_id != distributor.id
            ):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You cannot access this inventory ledger.",
                )

            return InventoryService.get_ledger(
                db=db,
                inventory_id=inventory_id,
            )

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
                or inventory.salesperson_id != salesperson.id
            ):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You cannot access this inventory ledger.",
                )

            return InventoryService.get_ledger(
                db=db,
                inventory_id=inventory_id,
            )

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient inventory access.",
        )

    except InventoryServiceError as exc:
        _handle_inventory_error(exc)


# ============================================================
# RECENT LEDGER
# ============================================================


# ============================================================
# OPENING STOCK
# ============================================================

@router.post(
    "/opening",
    response_model=InventoryResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_opening_stock(
    payload: InventoryMovementCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: User = Depends(require_permission("inventory.manage")),
):
    """
    Add opening stock to distributor inventory.

    distributor_id is intentionally NOT trusted from the
    request body. For distributor users it is derived from
    their authenticated account.
    """

    try:
        role = current_user.role.name

        if role == "DISTRIBUTOR":

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

            distributor_id = distributor.id

        elif role in {"SUPER ADMIN", "MASTER ADMIN"}:

            # Admin movement requires the target distributor
            # to be supplied through the request.
            distributor_id = payload.distributor_id

        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You cannot add opening stock.",
            )

        return InventoryService.add_opening_stock(
            db=db,
            distributor_id=distributor_id,
            product_id=payload.product_id,
            quantity=payload.quantity,
            performed_by=current_user.id,
            variant_id=payload.variant_id,
            reference_id=payload.reference_id,
            remarks=payload.remarks,
        )

    except InventoryServiceError as exc:
        db.rollback()
        _handle_inventory_error(exc)


# ============================================================
# RECEIVE STOCK
# ============================================================

@router.post(
    "/receive",
    response_model=InventoryResponse,
    status_code=status.HTTP_201_CREATED,
)
def receive_stock(
    payload: InventoryMovementCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: User = Depends(require_permission("inventory.manage")),
):
    """
    Add received stock to distributor inventory.
    """

    try:
        role = current_user.role.name

        if role == "DISTRIBUTOR":

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

            distributor_id = distributor.id

        elif role in {"SUPER ADMIN", "MASTER ADMIN"}:
            distributor_id = payload.distributor_id

        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You cannot receive stock.",
            )

        return InventoryService.receive_stock(
            db=db,
            distributor_id=distributor_id,
            product_id=payload.product_id,
            quantity=payload.quantity,
            performed_by=current_user.id,
            variant_id=payload.variant_id,
            reference_id=payload.reference_id,
            remarks=payload.remarks,
        )

    except InventoryServiceError as exc:
        db.rollback()
        _handle_inventory_error(exc)


# ============================================================
# STOCK ADJUSTMENT
# ============================================================

@router.post(
    "/adjust",
    response_model=InventoryResponse,
)
def adjust_stock(
    payload: InventoryMovementCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: User = Depends(require_permission("inventory.manage")),
):
    """
    Adjust stock.

    Positive quantity:
        Increase stock.

    Negative quantity:
        Decrease stock.
    """

    try:
        role = current_user.role.name

        if role == "DISTRIBUTOR":

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

            distributor_id = distributor.id

        elif role in {"SUPER ADMIN", "MASTER ADMIN"}:
            distributor_id = payload.distributor_id

        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You cannot adjust inventory.",
            )

        return InventoryService.adjust_stock(
            db=db,
            distributor_id=distributor_id,
            product_id=payload.product_id,
            quantity=payload.quantity,
            performed_by=current_user.id,
            salesperson_id=payload.salesperson_id,
            variant_id=payload.variant_id,
            reference_id=payload.reference_id,
            remarks=payload.remarks,
        )

    except InventoryServiceError as exc:
        db.rollback()
        _handle_inventory_error(exc)


# ============================================================
# DAMAGE
# ============================================================

@router.post(
    "/damage",
    response_model=InventoryResponse,
)
def record_damage(
    payload: InventoryMovementCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: User = Depends(require_permission("inventory.manage")),
):
    """
    Record damaged stock.
    """

    try:
        role = current_user.role.name

        if role == "DISTRIBUTOR":

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

            distributor_id = distributor.id

        elif role in {"SUPER ADMIN", "MASTER ADMIN"}:
            distributor_id = payload.distributor_id

        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You cannot record inventory damage.",
            )

        return InventoryService.record_damage(
            db=db,
            distributor_id=distributor_id,
            product_id=payload.product_id,
            quantity=payload.quantity,
            performed_by=current_user.id,
            salesperson_id=payload.salesperson_id,
            variant_id=payload.variant_id,
            reference_id=payload.reference_id,
            remarks=payload.remarks,
        )

    except InventoryServiceError as exc:
        db.rollback()
        _handle_inventory_error(exc)