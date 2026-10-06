from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator


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

    # --------------------------------------------------------
    # Geography
    #
    # New:
    #   state_id
    #   zone_ids[]
    #   area_ids[]
    #
    # Legacy zone_id / area_id are retained temporarily so
    # existing admin clients do not immediately break.
    # --------------------------------------------------------

    state_id: UUID

    zone_ids: list[UUID] = Field(
        default_factory=list,
    )

    area_ids: list[UUID] = Field(
        default_factory=list,
    )

    # Legacy compatibility
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

    @model_validator(mode="after")
    def validate_territory_input(self):
        # Support old payload:
        #
        # {
        #   "zone_id": "...",
        #   "area_id": "..."
        # }
        #
        # by converting it into the new arrays.

        if not self.zone_ids and self.zone_id is not None:
            self.zone_ids = [self.zone_id]

        if not self.area_ids and self.area_id is not None:
            self.area_ids = [self.area_id]

        if not self.zone_ids:
            raise ValueError(
                "At least one zone must be assigned"
            )

        if not self.area_ids:
            raise ValueError(
                "At least one area must be assigned"
            )

        # Remove duplicates while preserving order.
        self.zone_ids = list(
            dict.fromkeys(self.zone_ids)
        )

        self.area_ids = list(
            dict.fromkeys(self.area_ids)
        )

        return self


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

    zone_ids: list[UUID] | None = None
    area_ids: list[UUID] | None = None

    # Legacy compatibility
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

    @model_validator(mode="after")
    def normalize_territory_input(self):
        if (
            self.zone_ids is not None
            and self.zone_id is not None
        ):
            raise ValueError(
                "Use zone_ids or zone_id, not both"
            )

        if (
            self.area_ids is not None
            and self.area_id is not None
        ):
            raise ValueError(
                "Use area_ids or area_id, not both"
            )

        if self.zone_ids is not None:
            self.zone_ids = list(
                dict.fromkeys(self.zone_ids)
            )

        if self.area_ids is not None:
            self.area_ids = list(
                dict.fromkeys(self.area_ids)
            )

        return self


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

    # New territory representation
    zone_ids: list[UUID] = Field(
        default_factory=list,
    )

    area_ids: list[UUID] = Field(
        default_factory=list,
    )

    # Legacy fields retained for compatibility.
    # These represent the first assigned zone/area.
    zone_id: UUID | None
    area_id: UUID | None

    gst_number: str | None
    license_number: str | None

    credit_limit: Decimal | None

    user_id: UUID | None

    is_active: bool