from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.inventory.models import (
    Inventory,
    InventoryLedger,
    InventoryMovementType,
)
from app.inventory.repository import (
    create_inventory,
    create_ledger_entry,
    get_inventory,
    get_inventory_by_id,
    get_inventory_by_distributor,
    get_inventory_ledger,
    get_recent_ledger_entries,
    get_salesperson_inventory,
)


class InventoryServiceError(Exception):
    """Base exception for inventory business errors."""


class InventoryNotFoundError(InventoryServiceError):
    """Inventory record does not exist."""


class InsufficientStockError(InventoryServiceError):
    """Requested movement would make stock negative."""


class InvalidInventoryMovementError(InventoryServiceError):
    """Inventory movement is not valid."""


class InventoryScopeError(InventoryServiceError):
    """User is not allowed to operate on this inventory."""


class InventoryService:
    """
    Business logic for distributor and salesperson inventory.

    Repository:
        Database access only.

    Service:
        Validation + stock calculations + ledger creation.

    Router:
        HTTP/authentication layer.
    """

    # --------------------------------------------------------
    # MOVEMENT RULES
    # --------------------------------------------------------

    POSITIVE_MOVEMENTS = {
        InventoryMovementType.OPENING,
        InventoryMovementType.RECEIVED,
        InventoryMovementType.RETURN,
    }

    NEGATIVE_MOVEMENTS = {
        InventoryMovementType.ISSUED,
        InventoryMovementType.SALE,
        InventoryMovementType.DAMAGE,
    }

    # --------------------------------------------------------
    # BASIC INVENTORY READS
    # --------------------------------------------------------

    @staticmethod
    def get_inventory(
        db: Session,
        inventory_id: UUID,
    ) -> Inventory:

        inventory = get_inventory_by_id(
            db=db,
            inventory_id=inventory_id,
        )

        if inventory is None:
            raise InventoryNotFoundError(
                "Inventory record not found."
            )

        return inventory

    @staticmethod
    def list_distributor_inventory(
        db: Session,
        distributor_id: UUID,
    ) -> list[Inventory]:

        return get_inventory_by_distributor(
            db=db,
            distributor_id=distributor_id,
        )

    @staticmethod
    def list_salesperson_inventory(
        db: Session,
        distributor_id: UUID,
        salesperson_id: UUID,
    ) -> list[Inventory]:

        return get_salesperson_inventory(
            db=db,
            distributor_id=distributor_id,
            salesperson_id=salesperson_id,
        )

    @staticmethod
    def get_ledger(
        db: Session,
        inventory_id: UUID,
    ) -> list[InventoryLedger]:

        inventory = get_inventory_by_id(
            db=db,
            inventory_id=inventory_id,
        )

        if inventory is None:
            raise InventoryNotFoundError(
                "Inventory record not found."
            )

        return get_inventory_ledger(
            db=db,
            inventory_id=inventory_id,
        )

    @staticmethod
    def get_recent_ledger(
        db: Session,
        distributor_id: UUID,
        limit: int = 100,
    ) -> list[InventoryLedger]:

        if limit < 1:
            raise InvalidInventoryMovementError(
                "Limit must be greater than zero."
            )

        if limit > 500:
            limit = 500

        return get_recent_ledger_entries(
            db=db,
            distributor_id=distributor_id,
            limit=limit,
        )

    # --------------------------------------------------------
    # INTERNAL HELPERS
    # --------------------------------------------------------

    @staticmethod
    def _calculate_delta(
        movement_type: InventoryMovementType,
        quantity: Decimal,
    ) -> Decimal:

        if quantity == 0:
            raise InvalidInventoryMovementError(
                "Inventory quantity cannot be zero."
            )

        if movement_type in InventoryService.POSITIVE_MOVEMENTS:
            if quantity < 0:
                raise InvalidInventoryMovementError(
                    f"{movement_type.value} quantity must be positive."
                )

            return quantity

        if movement_type in InventoryService.NEGATIVE_MOVEMENTS:
            if quantity < 0:
                raise InvalidInventoryMovementError(
                    f"{movement_type.value} quantity must be positive."
                )

            return -quantity

        if movement_type == InventoryMovementType.ADJUSTMENT:
            # Adjustment is intentionally signed.
            #
            # +10 = increase stock by 10
            # -10 = decrease stock by 10
            return quantity

        raise InvalidInventoryMovementError(
            f"Unsupported inventory movement type: "
            f"{movement_type.value}"
        )

    @staticmethod
    def _validate_stock(
        current_quantity: Decimal,
        delta: Decimal,
    ) -> Decimal:

        new_quantity = current_quantity + delta

        if new_quantity < 0:
            raise InsufficientStockError(
                "Insufficient stock for this inventory movement."
            )

        return new_quantity

    @staticmethod
    def _create_inventory_position(
        db: Session,
        distributor_id: UUID,
        product_id: UUID,
        salesperson_id: UUID | None,
        variant_id: UUID | None,
    ) -> Inventory:

        inventory = Inventory(
            id=uuid4(),
            distributor_id=distributor_id,
            salesperson_id=salesperson_id,
            product_id=product_id,
            variant_id=variant_id,
            quantity=Decimal("0"),
        )

        try:
            return create_inventory(
                db=db,
                inventory=inventory,
            )

        except IntegrityError as exc:
            raise InvalidInventoryMovementError(
                "Unable to create inventory position."
            ) from exc

    @staticmethod
    def _get_or_create_inventory(
        db: Session,
        distributor_id: UUID,
        product_id: UUID,
        salesperson_id: UUID | None,
        variant_id: UUID | None,
    ) -> Inventory:

        inventory = get_inventory(
            db=db,
            distributor_id=distributor_id,
            product_id=product_id,
            salesperson_id=salesperson_id,
            variant_id=variant_id,
        )

        if inventory is not None:
            return inventory

        return InventoryService._create_inventory_position(
            db=db,
            distributor_id=distributor_id,
            product_id=product_id,
            salesperson_id=salesperson_id,
            variant_id=variant_id,
        )

    # --------------------------------------------------------
    # APPLY SINGLE INVENTORY MOVEMENT
    # --------------------------------------------------------

    @staticmethod
    def apply_movement(
        db: Session,
        *,
        distributor_id: UUID,
        product_id: UUID,
        quantity: Decimal,
        movement_type: InventoryMovementType,
        performed_by: UUID,
        salesperson_id: UUID | None = None,
        variant_id: UUID | None = None,
        source: str | None = None,
        destination: str | None = None,
        reference_id: UUID | None = None,
        remarks: str | None = None,
    ) -> Inventory:

        if quantity == 0:
            raise InvalidInventoryMovementError(
                "Quantity cannot be zero."
            )

        delta = InventoryService._calculate_delta(
            movement_type=movement_type,
            quantity=quantity,
        )

        inventory = InventoryService._get_or_create_inventory(
            db=db,
            distributor_id=distributor_id,
            product_id=product_id,
            salesperson_id=salesperson_id,
            variant_id=variant_id,
        )

        new_quantity = InventoryService._validate_stock(
            current_quantity=inventory.quantity,
            delta=delta,
        )

        inventory.quantity = new_quantity

        ledger = InventoryLedger(
            id=uuid4(),
            inventory_id=inventory.id,
            product_id=product_id,
            variant_id=variant_id,
            quantity=delta,
            movement_type=movement_type,
            source=source,
            destination=destination,
            reference_id=reference_id,
            performed_by=performed_by,
            remarks=remarks,
        )

        create_ledger_entry(
            db=db,
            ledger=ledger,
        )

        db.flush()

        return inventory

    # --------------------------------------------------------
    # DISTRIBUTOR → SALESPERSON STOCK TRANSFER
    # --------------------------------------------------------

    @staticmethod
    def issue_stock_to_salesperson(
        db: Session,
        *,
        distributor_id: UUID,
        salesperson_id: UUID,
        product_id: UUID,
        quantity: Decimal,
        performed_by: UUID,
        variant_id: UUID | None = None,
        reference_id: UUID | None = None,
        remarks: str | None = None,
    ) -> tuple[Inventory, Inventory]:

        if quantity <= 0:
            raise InvalidInventoryMovementError(
                "Issued quantity must be greater than zero."
            )

        # ----------------------------------------------------
        # SOURCE: DISTRIBUTOR STOCK
        # ----------------------------------------------------

        distributor_inventory = InventoryService._get_or_create_inventory(
            db=db,
            distributor_id=distributor_id,
            product_id=product_id,
            salesperson_id=None,
            variant_id=variant_id,
        )

        distributor_new_quantity = (
            distributor_inventory.quantity - quantity
        )

        if distributor_new_quantity < 0:
            raise InsufficientStockError(
                "Distributor does not have enough stock."
            )

        # ----------------------------------------------------
        # DESTINATION: SALESPERSON STOCK
        # ----------------------------------------------------

        salesperson_inventory = InventoryService._get_or_create_inventory(
            db=db,
            distributor_id=distributor_id,
            product_id=product_id,
            salesperson_id=salesperson_id,
            variant_id=variant_id,
        )

        salesperson_new_quantity = (
            salesperson_inventory.quantity + quantity
        )

        # ----------------------------------------------------
        # UPDATE BOTH POSITIONS
        # ----------------------------------------------------

        distributor_inventory.quantity = (
            distributor_new_quantity
        )

        salesperson_inventory.quantity = (
            salesperson_new_quantity
        )

        # ----------------------------------------------------
        # SHARED REFERENCE
        # ----------------------------------------------------

        transfer_reference = reference_id or uuid4()

        # Distributor side
        distributor_ledger = InventoryLedger(
            id=uuid4(),
            inventory_id=distributor_inventory.id,
            product_id=product_id,
            variant_id=variant_id,
            quantity=-quantity,
            movement_type=InventoryMovementType.ISSUED,
            source="DISTRIBUTOR",
            destination="SALESPERSON",
            reference_id=transfer_reference,
            performed_by=performed_by,
            remarks=remarks,
        )

        # Salesperson side
        salesperson_ledger = InventoryLedger(
            id=uuid4(),
            inventory_id=salesperson_inventory.id,
            product_id=product_id,
            variant_id=variant_id,
            quantity=quantity,
            movement_type=InventoryMovementType.ISSUED,
            source="DISTRIBUTOR",
            destination="SALESPERSON",
            reference_id=transfer_reference,
            performed_by=performed_by,
            remarks=remarks,
        )

        create_ledger_entry(
            db=db,
            ledger=distributor_ledger,
        )

        create_ledger_entry(
            db=db,
            ledger=salesperson_ledger,
        )

        db.flush()

        return (
            distributor_inventory,
            salesperson_inventory,
        )

    # --------------------------------------------------------
    # SALE STOCK DEDUCTION
    # --------------------------------------------------------

    @staticmethod
    def deduct_sale_stock(
        db: Session,
        *,
        distributor_id: UUID,
        product_id: UUID,
        quantity: Decimal,
        performed_by: UUID,
        salesperson_id: UUID | None = None,
        variant_id: UUID | None = None,
        reference_id: UUID | None = None,
        remarks: str | None = None,
    ) -> Inventory:

        if quantity <= 0:
            raise InvalidInventoryMovementError(
                "Sale quantity must be greater than zero."
            )

        return InventoryService.apply_movement(
            db=db,
            distributor_id=distributor_id,
            product_id=product_id,
            salesperson_id=salesperson_id,
            variant_id=variant_id,
            quantity=quantity,
            movement_type=InventoryMovementType.SALE,
            performed_by=performed_by,
            source="INVENTORY",
            destination="SALE",
            reference_id=reference_id,
            remarks=remarks,
        )

    # --------------------------------------------------------
    # STOCK ADJUSTMENT
    # --------------------------------------------------------

    @staticmethod
    def adjust_stock(
        db: Session,
        *,
        distributor_id: UUID,
        product_id: UUID,
        quantity: Decimal,
        performed_by: UUID,
        salesperson_id: UUID | None = None,
        variant_id: UUID | None = None,
        reference_id: UUID | None = None,
        remarks: str | None = None,
    ) -> Inventory:

        if quantity == 0:
            raise InvalidInventoryMovementError(
                "Adjustment quantity cannot be zero."
            )

        return InventoryService.apply_movement(
            db=db,
            distributor_id=distributor_id,
            product_id=product_id,
            salesperson_id=salesperson_id,
            variant_id=variant_id,
            quantity=quantity,
            movement_type=InventoryMovementType.ADJUSTMENT,
            performed_by=performed_by,
            source="ADJUSTMENT",
            destination="INVENTORY",
            reference_id=reference_id,
            remarks=remarks,
        )

    # --------------------------------------------------------
    # OPENING STOCK
    # --------------------------------------------------------

    @staticmethod
    def add_opening_stock(
        db: Session,
        *,
        distributor_id: UUID,
        product_id: UUID,
        quantity: Decimal,
        performed_by: UUID,
        variant_id: UUID | None = None,
        reference_id: UUID | None = None,
        remarks: str | None = None,
    ) -> Inventory:

        if quantity <= 0:
            raise InvalidInventoryMovementError(
                "Opening quantity must be greater than zero."
            )

        return InventoryService.apply_movement(
            db=db,
            distributor_id=distributor_id,
            product_id=product_id,
            quantity=quantity,
            movement_type=InventoryMovementType.OPENING,
            performed_by=performed_by,
            salesperson_id=None,
            variant_id=variant_id,
            source="OPENING",
            destination="DISTRIBUTOR",
            reference_id=reference_id,
            remarks=remarks,
        )

    # --------------------------------------------------------
    # RECEIVED STOCK
    # --------------------------------------------------------

    @staticmethod
    def receive_stock(
        db: Session,
        *,
        distributor_id: UUID,
        product_id: UUID,
        quantity: Decimal,
        performed_by: UUID,
        variant_id: UUID | None = None,
        reference_id: UUID | None = None,
        remarks: str | None = None,
    ) -> Inventory:

        if quantity <= 0:
            raise InvalidInventoryMovementError(
                "Received quantity must be greater than zero."
            )

        return InventoryService.apply_movement(
            db=db,
            distributor_id=distributor_id,
            product_id=product_id,
            quantity=quantity,
            movement_type=InventoryMovementType.RECEIVED,
            performed_by=performed_by,
            salesperson_id=None,
            variant_id=variant_id,
            source="SUPPLIER",
            destination="DISTRIBUTOR",
            reference_id=reference_id,
            remarks=remarks,
        )

    # --------------------------------------------------------
    # DAMAGE STOCK
    # --------------------------------------------------------

    @staticmethod
    def record_damage(
        db: Session,
        *,
        distributor_id: UUID,
        product_id: UUID,
        quantity: Decimal,
        performed_by: UUID,
        salesperson_id: UUID | None = None,
        variant_id: UUID | None = None,
        reference_id: UUID | None = None,
        remarks: str | None = None,
    ) -> Inventory:

        if quantity <= 0:
            raise InvalidInventoryMovementError(
                "Damage quantity must be greater than zero."
            )

        return InventoryService.apply_movement(
            db=db,
            distributor_id=distributor_id,
            product_id=product_id,
            quantity=quantity,
            movement_type=InventoryMovementType.DAMAGE,
            performed_by=performed_by,
            salesperson_id=salesperson_id,
            variant_id=variant_id,
            source="INVENTORY",
            destination="DAMAGE",
            reference_id=reference_id,
            remarks=remarks,
        )