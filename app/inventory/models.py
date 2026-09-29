from datetime import datetime
from decimal import Decimal
from enum import Enum
from uuid import UUID as PyUUID

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class InventoryMovementType(str, Enum):
    OPENING = "OPENING"
    RECEIVED = "RECEIVED"
    ISSUED = "ISSUED"
    SALE = "SALE"
    RETURN = "RETURN"
    DAMAGE = "DAMAGE"
    ADJUSTMENT = "ADJUSTMENT"


class Inventory(Base):
    __tablename__ = "inventory"

    id: Mapped[PyUUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
    )

    distributor_id: Mapped[PyUUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("distributors.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    salesperson_id: Mapped[PyUUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("salespersons.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )

    product_id: Mapped[PyUUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("products.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    variant_id: Mapped[PyUUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("product_variants.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )

    quantity: Mapped[Decimal] = mapped_column(
        Numeric(14, 3),
        nullable=False,
        default=0,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default="now()",
    )

    __table_args__ = (
    Index(
        "uq_inventory_distributor_no_variant",
        "distributor_id",
        "product_id",
        unique=True,
        postgresql_where=(
            salesperson_id.is_(None) & variant_id.is_(None)
        ),
    ),
    Index(
        "uq_inventory_distributor_variant",
        "distributor_id",
        "product_id",
        "variant_id",
        unique=True,
        postgresql_where=(
            salesperson_id.is_(None) & variant_id.is_not(None)
        ),
    ),
    Index(
        "uq_inventory_salesperson_no_variant",
        "distributor_id",
        "salesperson_id",
        "product_id",
        unique=True,
        postgresql_where=(
            salesperson_id.is_not(None) & variant_id.is_(None)
        ),
    ),
    Index(
        "uq_inventory_salesperson_variant",
        "distributor_id",
        "salesperson_id",
        "product_id",
        "variant_id",
        unique=True,
        postgresql_where=(
            salesperson_id.is_not(None) & variant_id.is_not(None)
        ),
    ),
)


class InventoryLedger(Base):
    __tablename__ = "inventory_ledger"

    id: Mapped[PyUUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
    )

    inventory_id: Mapped[PyUUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("inventory.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    product_id: Mapped[PyUUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("products.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    variant_id: Mapped[PyUUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("product_variants.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )

    quantity: Mapped[Decimal] = mapped_column(
        Numeric(14, 3),
        nullable=False,
    )

    movement_type: Mapped[InventoryMovementType] = mapped_column(
        SAEnum(
            InventoryMovementType,
            name="inventorymovementtype",
        ),
        nullable=False,
    )

    source: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    destination: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    reference_id: Mapped[PyUUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        index=True,
    )

    performed_by: Mapped[PyUUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    remarks: Mapped[str | None] = mapped_column(
        String(1000),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default="now()",
        index=True,
    )