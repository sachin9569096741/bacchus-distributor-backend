from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.inventory.models import InventoryMovementType


class InventoryMovementCreate(BaseModel):
    distributor_id: UUID
    salesperson_id: UUID | None = None
    product_id: UUID
    variant_id: UUID | None = None

    quantity: Decimal = Field(gt=0, max_digits=14, decimal_places=3)

    movement_type: InventoryMovementType

    source: str | None = Field(default=None, max_length=100)
    destination: str | None = Field(default=None, max_length=100)
    reference_id: UUID | None = None
    remarks: str | None = Field(default=None, max_length=1000)


class InventoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    distributor_id: UUID
    salesperson_id: UUID | None
    product_id: UUID
    variant_id: UUID | None
    quantity: Decimal
    updated_at: datetime


class InventoryLedgerResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    inventory_id: UUID
    product_id: UUID
    variant_id: UUID | None
    quantity: Decimal
    movement_type: InventoryMovementType
    source: str | None
    destination: str | None
    reference_id: UUID | None
    performed_by: UUID
    remarks: str | None
    created_at: datetime