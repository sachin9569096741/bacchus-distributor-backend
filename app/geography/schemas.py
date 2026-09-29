from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class StateCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    code: str = Field(min_length=2, max_length=20)


class StateUpdate(BaseModel):
    name: str | None = Field(
        default=None,
        min_length=2,
        max_length=100,
    )
    code: str | None = Field(
        default=None,
        min_length=2,
        max_length=20,
    )
    is_active: bool | None = None


class StateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    code: str
    is_active: bool


class ZoneCreate(BaseModel):
    state_id: UUID
    name: str = Field(min_length=2, max_length=100)
    code: str = Field(min_length=2, max_length=20)


class ZoneUpdate(BaseModel):
    name: str | None = Field(
        default=None,
        min_length=2,
        max_length=100,
    )
    code: str | None = Field(
        default=None,
        min_length=2,
        max_length=20,
    )
    is_active: bool | None = None


class ZoneResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    state_id: UUID
    name: str
    code: str
    is_active: bool


class AreaCreate(BaseModel):
    state_id: UUID
    zone_id: UUID
    name: str = Field(min_length=2, max_length=100)
    code: str = Field(min_length=2, max_length=20)


class AreaUpdate(BaseModel):
    name: str | None = Field(
        default=None,
        min_length=2,
        max_length=100,
    )
    code: str | None = Field(
        default=None,
        min_length=2,
        max_length=20,
    )
    is_active: bool | None = None


class AreaResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    state_id: UUID
    zone_id: UUID
    name: str
    code: str
    is_active: bool