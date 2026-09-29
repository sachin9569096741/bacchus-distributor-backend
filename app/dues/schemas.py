from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.dues.models import DueEntryType


class DueEntryCreate(BaseModel):
    seller_id: UUID
    distributor_id: UUID | None = None

    entry_type: DueEntryType
    amount: Decimal = Field(
        gt=0,
        max_digits=14,
        decimal_places=2,
    )

    reference_id: UUID | None = None
    reference_type: str | None = Field(
        default=None,
        max_length=50,
    )
    remarks: str | None = Field(
        default=None,
        max_length=2000,
    )


class DueEntryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    seller_id: UUID
    distributor_id: UUID
    entry_type: DueEntryType
    amount: Decimal
    reference_id: UUID | None
    reference_type: str | None
    remarks: str | None
    created_by: UUID
    created_at: datetime


class DueSummaryResponse(BaseModel):
    seller_id: UUID
    distributor_id: UUID

    total_credit_sales: Decimal
    total_verified_payments: Decimal
    total_adjustments: Decimal

    outstanding: Decimal