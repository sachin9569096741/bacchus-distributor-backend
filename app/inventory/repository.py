from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.inventory.models import (
    Inventory,
    InventoryLedger,
    InventoryMovementType,
)


# ============================================================
# INVENTORY
# ============================================================

def get_inventory_by_id(
    db: Session,
    inventory_id: UUID,
) -> Inventory | None:
    return db.scalar(
        select(Inventory).where(
            Inventory.id == inventory_id
        )
    )


def get_inventory(
    db: Session,
    distributor_id: UUID,
    product_id: UUID,
    salesperson_id: UUID | None = None,
    variant_id: UUID | None = None,
) -> Inventory | None:

    stmt = select(Inventory).where(
        Inventory.distributor_id == distributor_id,
        Inventory.product_id == product_id,
    )

    if salesperson_id is None:
        stmt = stmt.where(
            Inventory.salesperson_id.is_(None)
        )
    else:
        stmt = stmt.where(
            Inventory.salesperson_id == salesperson_id
        )

    if variant_id is None:
        stmt = stmt.where(
            Inventory.variant_id.is_(None)
        )
    else:
        stmt = stmt.where(
            Inventory.variant_id == variant_id
        )

    return db.scalar(stmt)


def get_distributor_inventory(
    db: Session,
    distributor_id: UUID,
) -> list[Inventory]:

    return list(
        db.scalars(
            select(Inventory)
            .where(
                Inventory.distributor_id == distributor_id,
                Inventory.salesperson_id.is_(None),
            )
            .order_by(Inventory.updated_at.desc())
        ).all()
    )


def get_salesperson_inventory(
    db: Session,
    distributor_id: UUID,
    salesperson_id: UUID,
) -> list[Inventory]:

    return list(
        db.scalars(
            select(Inventory)
            .where(
                Inventory.distributor_id == distributor_id,
                Inventory.salesperson_id == salesperson_id,
            )
            .order_by(Inventory.updated_at.desc())
        ).all()
    )


def get_inventory_by_distributor(
    db: Session,
    distributor_id: UUID,
) -> list[Inventory]:

    return list(
        db.scalars(
            select(Inventory)
            .where(
                Inventory.distributor_id == distributor_id
            )
            .order_by(Inventory.updated_at.desc())
        ).all()
    )


def get_inventory_by_product(
    db: Session,
    distributor_id: UUID,
    product_id: UUID,
) -> list[Inventory]:

    return list(
        db.scalars(
            select(Inventory)
            .where(
                Inventory.distributor_id == distributor_id,
                Inventory.product_id == product_id,
            )
            .order_by(Inventory.updated_at.desc())
        ).all()
    )


def create_inventory(
    db: Session,
    inventory: Inventory,
) -> Inventory:

    db.add(inventory)
    db.flush()

    return inventory


def save_inventory(
    db: Session,
    inventory: Inventory,
) -> Inventory:

    db.add(inventory)
    db.flush()

    return inventory


# ============================================================
# INVENTORY LEDGER
# ============================================================

def create_ledger_entry(
    db: Session,
    ledger: InventoryLedger,
) -> InventoryLedger:

    db.add(ledger)
    db.flush()

    return ledger


def get_ledger_entry_by_id(
    db: Session,
    ledger_id: UUID,
) -> InventoryLedger | None:

    return db.scalar(
        select(InventoryLedger).where(
            InventoryLedger.id == ledger_id
        )
    )


def get_inventory_ledger(
    db: Session,
    inventory_id: UUID,
) -> list[InventoryLedger]:

    return list(
        db.scalars(
            select(InventoryLedger)
            .where(
                InventoryLedger.inventory_id == inventory_id
            )
            .order_by(
                InventoryLedger.created_at.desc()
            )
        ).all()
    )


def get_ledger_by_reference(
    db: Session,
    reference_id: UUID,
) -> list[InventoryLedger]:

    return list(
        db.scalars(
            select(InventoryLedger)
            .where(
                InventoryLedger.reference_id == reference_id
            )
            .order_by(
                InventoryLedger.created_at.desc()
            )
        ).all()
    )


def get_ledger_by_movement_type(
    db: Session,
    inventory_id: UUID,
    movement_type: InventoryMovementType,
) -> list[InventoryLedger]:

    return list(
        db.scalars(
            select(InventoryLedger)
            .where(
                InventoryLedger.inventory_id == inventory_id,
                InventoryLedger.movement_type == movement_type,
            )
            .order_by(
                InventoryLedger.created_at.desc()
            )
        ).all()
    )


def get_recent_ledger_entries(
    db: Session,
    distributor_id: UUID,
    limit: int = 100,
) -> list[InventoryLedger]:

    return list(
        db.scalars(
            select(InventoryLedger)
            .join(
                Inventory,
                Inventory.id == InventoryLedger.inventory_id,
            )
            .where(
                Inventory.distributor_id == distributor_id
            )
            .order_by(
                InventoryLedger.created_at.desc()
            )
            .limit(limit)
        ).all()
    )