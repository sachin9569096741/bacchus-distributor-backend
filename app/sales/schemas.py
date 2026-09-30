from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


# ============================================================
# SALE ITEM
# ============================================================

class SaleItemCreate(BaseModel):
    product_id: UUID

    variant_id: UUID | None = None

    quantity: Decimal = Field(
        gt=0,
        max_digits=14,
        decimal_places=3,
    )

    selling_price: Decimal = Field(
        ge=0,
        max_digits=14,
        decimal_places=2,
    )


class SaleItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    sale_id: UUID
    product_id: UUID
    variant_id: UUID | None

    quantity: Decimal
    selling_price: Decimal
    line_total: Decimal


# ============================================================
# CREATE SALE
# ============================================================

class SaleCreate(BaseModel):
    """
    Create a sale.

    SALESPERSON:
        distributor_id and salesperson_id are derived
        from the authenticated user.

    MASTER ADMIN / SUPER ADMIN:
        distributor_id and salesperson_id must be supplied
        from the frontend.

    Seller relationship, territory and ownership are
    validated server-side by SaleService.
    """

    seller_id: UUID

    # Required for ADMIN.
    # Ignored/derived for SALESPERSON.
    distributor_id: UUID | None = None

    # Required for ADMIN.
    # Ignored/derived for SALESPERSON.
    salesperson_id: UUID | None = None

    sale_date: date

    items: list[SaleItemCreate] = Field(
        min_length=1,
        max_length=100,
    )

    remarks: str | None = Field(
        default=None,
        max_length=2000,
    )


# ============================================================
# SALE RESPONSE
# ============================================================

class SaleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    sale_number: str

    seller_id: UUID
    salesperson_id: UUID
    distributor_id: UUID

    sale_date: date
    total_amount: Decimal

    remarks: str | None

    created_by: UUID
    created_at: datetime

    items: list[SaleItemResponse] = Field(
        default_factory=list
    )