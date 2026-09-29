from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class AuditLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    actor_id: UUID | None
    action: str
    entity: str
    entity_id: UUID | None
    ip_address: str | None
    old_value: dict | None
    new_value: dict | None
    created_at: datetime


class AuditLogFilter(BaseModel):
    actor_id: UUID | None = None
    action: str | None = Field(default=None, max_length=100)
    entity: str | None = Field(default=None, max_length=100)
    entity_id: UUID | None = None
    limit: int = Field(default=100, ge=1, le=500)
    offset: int = Field(default=0, ge=0)