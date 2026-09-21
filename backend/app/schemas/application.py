import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ApplicationCreate(BaseModel):
    project_id: uuid.UUID
    name: str
    description: str | None = None
    default_requires_client_approval: bool = False


class ApplicationUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    default_requires_client_approval: bool | None = None


class ApplicationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    project_id: uuid.UUID
    name: str
    description: str | None
    default_requires_client_approval: bool
    is_active: bool
    created_by: uuid.UUID
    created_at: datetime
    updated_at: datetime
