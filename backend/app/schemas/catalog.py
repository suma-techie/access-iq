import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class CatalogEntryCreate(BaseModel):
    permission_name: str
    permission_key: str
    description: str | None = None
    severity: str
    requires_client_approval: bool | None = None


class CatalogEntryUpdate(BaseModel):
    permission_name: str | None = None
    description: str | None = None
    severity: str | None = None
    requires_client_approval: bool | None = None


class CatalogEntryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    application_id: uuid.UUID
    permission_name: str
    permission_key: str
    description: str | None
    severity: str
    requires_client_approval: bool | None
    is_active: bool
    created_by: uuid.UUID
    created_at: datetime
    updated_at: datetime
