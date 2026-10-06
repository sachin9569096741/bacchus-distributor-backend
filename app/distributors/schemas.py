from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


# ============================================================
# TERRITORY REFERENCES
# ============================================================


class TerritoryReference(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    code: str


# ============================================================
# DISTRIBUTOR CREATE
# ============================================================


class DistributorCreate(BaseModel):
    business_name: str = Field(..., min_length=2, max_length=255)
    owner_name: str = Field(..., min_length=2, max_length=255)

    mobile: str = Field(..., min_length=5, max_length=30)
    email: EmailStr

    password: str = Field(..., min_length=8)

    address: str = Field(..., min_length=2)

    state_id: UUID

    zone_ids: list[UUID] = Field(default_factory=list)
    area_ids: list[UUID] = Field(default_factory=list)

    # Legacy compatibility
    zone_id: UUID | None = None
    area_id: UUID | None = None

    gst_number: str | None = None
    license_number: str | None = None

    credit_limit: Decimal | None = None

    @field_validator("zone_ids", mode="before")
    @classmethod
    def normalize_zone_ids(cls, value):
        if value is None:
            return []

        if isinstance(value, UUID):
            return [value]

        return value

    @field_validator("area_ids", mode="before")
    @classmethod
    def normalize_area_ids(cls, value):
        if value is None:
            return []

        if isinstance(value, UUID):
            return [value]

        return value

    def model_post_init(self, __context):
        if not self.zone_ids and self.zone_id:
            self.zone_ids = [self.zone_id]

        if not self.area_ids and self.area_id:
            self.area_ids = [self.area_id]

        if not self.zone_ids:
            raise ValueError("At least one zone must be assigned")

        if not self.area_ids:
            raise ValueError("At least one area must be assigned")


# ============================================================
# DISTRIBUTOR UPDATE
# ============================================================


class DistributorUpdate(BaseModel):
    business_name: str | None = None
    owner_name: str | None = None

    mobile: str | None = None
    email: EmailStr | None = None

    address: str | None = None

    state_id: UUID | None = None

    zone_ids: list[UUID] | None = None
    area_ids: list[UUID] | None = None

    # Legacy compatibility
    zone_id: UUID | None = None
    area_id: UUID | None = None

    gst_number: str | None = None
    license_number: str | None = None

    credit_limit: Decimal | None = None

    is_active: bool | None = None

    @field_validator("zone_ids", mode="before")
    @classmethod
    def normalize_zone_ids(cls, value):
        if value is None:
            return None

        if isinstance(value, UUID):
            return [value]

        return value

    @field_validator("area_ids", mode="before")
    @classmethod
    def normalize_area_ids(cls, value):
        if value is None:
            return None

        if isinstance(value, UUID):
            return [value]

        return value


# ============================================================
# DISTRIBUTOR RESPONSE
# ============================================================


class DistributorResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID

    distributor_code: str

    business_name: str
    owner_name: str

    mobile: str
    email: EmailStr | None

    address: str

    # --------------------------------------------------------
    # State
    # --------------------------------------------------------

    state_id: UUID
    state: TerritoryReference

    # --------------------------------------------------------
    # New territory structure
    # --------------------------------------------------------

    zones: list[TerritoryReference] = Field(default_factory=list)
    areas: list[TerritoryReference] = Field(default_factory=list)

    zone_ids: list[UUID] = Field(default_factory=list)
    area_ids: list[UUID] = Field(default_factory=list)

    # --------------------------------------------------------
    # Legacy compatibility
    # --------------------------------------------------------

    zone_id: UUID | None = None
    area_id: UUID | None = None

    # --------------------------------------------------------
    # Business information
    # --------------------------------------------------------

    gst_number: str | None = None
    license_number: str | None = None

    credit_limit: Decimal | None = None

    user_id: UUID | None = None

    is_active: bool

    created_at: datetime
    updated_at: datetime


# ============================================================
# STATUS UPDATE
# ============================================================


class DistributorStatusUpdate(BaseModel):
    is_active: bool