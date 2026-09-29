from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.payment_proofs.models import PaymentProofStatus


class PaymentProofCreate(BaseModel):
    seller_id: UUID
    amount: Decimal = Field(
        gt=0,
        max_digits=14,
        decimal_places=2,
    )
    payment_id: str = Field(
        min_length=1,
        max_length=150,
    )
    screenshot_url: str = Field(
        min_length=1,
        max_length=5000,
    )
    payment_date: date
    remarks: str | None = Field(
        default=None,
        max_length=2000,
    )


class PaymentProofReject(BaseModel):
    rejection_reason: str = Field(
        min_length=1,
        max_length=2000,
    )


class PaymentProofResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    payment_proof_code: str

    seller_id: UUID
    salesperson_id: UUID
    distributor_id: UUID

    amount: Decimal
    payment_id: str
    screenshot_url: str
    payment_date: date
    remarks: str | None

    status: PaymentProofStatus

    submitted_by: UUID
    verified_by: UUID | None
    verified_at: datetime | None
    rejection_reason: str | None

    created_at: datetime
    updated_at: datetime