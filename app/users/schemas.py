from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class MasterAdminCreate(BaseModel):
    email: EmailStr
    mobile: str | None = Field(default=None, max_length=20)
    password: str = Field(min_length=8, max_length=72)


class MasterAdminUpdate(BaseModel):
    mobile: str | None = Field(default=None, max_length=20)
    is_active: bool | None = None


class MasterAdminResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: EmailStr
    mobile: str | None
    role_id: UUID
    is_active: bool