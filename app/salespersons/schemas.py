from datetime import date
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


# ============================================================
# CREATE SALESPERSON
# ============================================================

class SalespersonCreate(BaseModel):
    name: str = Field(
        min_length=2,
        max_length=150,
    )

    employee_code: str | None = Field(
        default=None,
        min_length=1,
        max_length=50,
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

    distributor_id: UUID
    state_id: UUID
    zone_id: UUID
    area_id: UUID

    joining_date: date | None = None


# ============================================================
# UPDATE SALESPERSON
# ============================================================

class SalespersonUpdate(BaseModel):
    name: str | None = Field(
        default=None,
        min_length=2,
        max_length=150,
    )

    employee_code: str | None = Field(
        default=None,
        min_length=1,
        max_length=50,
    )

    mobile: str | None = Field(
        default=None,
        min_length=7,
        max_length=20,
    )

    email: EmailStr | None = None

    state_id: UUID | None = None
    zone_id: UUID | None = None
    area_id: UUID | None = None

    joining_date: date | None = None


# ============================================================
# UPDATE STATUS
# ============================================================

class SalespersonStatusUpdate(BaseModel):
    is_active: bool


# ============================================================
# RESPONSE
# ============================================================

class SalespersonResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
    )

    id: UUID
    salesperson_code: str
    employee_code: str | None

    name: str
    mobile: str
    email: str | None

    distributor_id: UUID
    state_id: UUID
    zone_id: UUID
    area_id: UUID

    joining_date: date | None

    user_id: UUID

    is_active: bool