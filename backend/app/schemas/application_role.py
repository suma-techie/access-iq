import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ApplicationRoleCreate(BaseModel):
    user_id: uuid.UUID
    role_name: str


class ApplicationRoleUpdate(BaseModel):
    role_name: str


class ApplicationRoleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    application_id: uuid.UUID
    user_id: uuid.UUID
    role_name: str
    assigned_by: uuid.UUID
    assigned_at: datetime
    revoked_at: datetime | None
