from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.stock_requests.models import StockRequestStatus


# ============================================================
# STOCK REQUEST ITEM
# ============================================================

class StockRequestItemCreate(BaseModel):
    product_id: UUID
    variant_id: UUID | None = None

    quantity: Decimal = Field(
        gt=0,
        max_digits=14,
        decimal_places=3,
    )


class StockRequestItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    stock_request_id: UUID
    product_id: UUID
    variant_id: UUID | None
    quantity: Decimal


# ============================================================
# CREATE STOCK REQUEST
# ============================================================

class StockRequestCreate(BaseModel):
    """
    Created by salesperson.

    distributor_id and salesperson_id are intentionally
    not accepted from the frontend.

    They must be derived by the service from the
    authenticated salesperson.
    """

    items: list[StockRequestItemCreate] = Field(
        min_length=1,
        max_length=100,
    )

    remarks: str | None = Field(
        default=None,
        max_length=2000,
    )


# ============================================================
# REJECT STOCK REQUEST
# ============================================================

class StockRequestReject(BaseModel):
    rejection_reason: str = Field(
        min_length=1,
        max_length=2000,
    )


# ============================================================
# STOCK REQUEST RESPONSE
# ============================================================

class StockRequestResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    request_code: str

    distributor_id: UUID
    salesperson_id: UUID

    status: StockRequestStatus

    remarks: str | None

    reviewed_by: UUID | None
    reviewed_at: datetime | None

    rejection_reason: str | None

    created_at: datetime
    updated_at: datetime

    items: list[StockRequestItemResponse] = []