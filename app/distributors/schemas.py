from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


# ============================================================
# CREATE DISTRIBUTOR
# ============================================================

class DistributorCreate(BaseModel):
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

    email: EmailStr

    password: str = Field(
        min_length=8,
        max_length=72,
    )

    address: str = Field(
        min_length=3,
    )

    state_id: UUID
    zone_id: UUID
    area_id: UUID

    gst_number: str | None = Field(
        default=None,
        max_length=30,
    )

    license_number: str | None = Field(
        default=None,
        max_length=100,
    )

    credit_limit: Decimal | None = Field(
        default=None,
        ge=0,
        max_digits=14,
        decimal_places=2,
    )


# ============================================================
# UPDATE DISTRIBUTOR
# ============================================================

class DistributorUpdate(BaseModel):
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

    gst_number: str | None = Field(
        default=None,
        max_length=30,
    )

    license_number: str | None = Field(
        default=None,
        max_length=100,
    )

    credit_limit: Decimal | None = Field(
        default=None,
        ge=0,
        max_digits=14,
        decimal_places=2,
    )

    is_active: bool | None = None


# ============================================================
# UPDATE DISTRIBUTOR STATUS
# ============================================================

class DistributorStatusUpdate(BaseModel):
    is_active: bool


# ============================================================
# DISTRIBUTOR RESPONSE
# ============================================================

class DistributorResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
    )

    id: UUID

    distributor_code: str

    business_name: str
    owner_name: str

    mobile: str
    email: str | None

    address: str

    state_id: UUID
    zone_id: UUID
    area_id: UUID

    gst_number: str | None
    license_number: str | None

    credit_limit: Decimal | None

    user_id: UUID | None

    is_active: bool