from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class SellerCreate(BaseModel):
    business_name: str = Field(
        min_length=2,
        max_length=255,
    )

    owner_name: str = Field(
        min_length=2,
        max_length=150,
    )

    mobile: str = Field(
        min_length=7,
        max_length=20,
    )

    email: EmailStr | None = None

    address: str = Field(
        min_length=3,
    )

    state_id: UUID
    zone_id: UUID
    area_id: UUID

    distributor_id: UUID
    salesperson_id: UUID

    gst_number: str | None = Field(
        default=None,
        max_length=30,
    )

    credit_limit: Decimal | None = Field(
        default=None,
        ge=0,
        max_digits=14,
        decimal_places=2,
    )


class SellerUpdate(BaseModel):
    business_name: str | None = Field(
        default=None,
        min_length=2,
        max_length=255,
    )

    owner_name: str | None = Field(
        default=None,
        min_length=2,
        max_length=150,
    )

    mobile: str | None = Field(
        default=None,
        min_length=7,
        max_length=20,
    )

    email: EmailStr | None = None

    address: str | None = Field(
        default=None,
        min_length=3,
    )

    state_id: UUID | None = None
    zone_id: UUID | None = None
    area_id: UUID | None = None

    # Distributor and salesperson ownership
    # are intentionally NOT updateable here.
    gst_number: str | None = Field(
        default=None,
        max_length=30,
    )

    credit_limit: Decimal | None = Field(
        default=None,
        ge=0,
        max_digits=14,
        decimal_places=2,
    )


class SellerStatusUpdate(BaseModel):
    is_active: bool


class SellerResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    seller_code: str

    business_name: str
    owner_name: str

    mobile: str
    email: str | None

    address: str

    state_id: UUID
    zone_id: UUID
    area_id: UUID

    distributor_id: UUID
    salesperson_id: UUID

    gst_number: str | None
    credit_limit: Decimal | None

    is_active: bool