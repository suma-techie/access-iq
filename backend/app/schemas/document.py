import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class DocumentLinkCreate(BaseModel):
    file_type: str
    label: str
    url: str


class DocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    application_id: uuid.UUID
    uploaded_by: uuid.UUID
    original_filename: str
    file_type: str
    storage_url: str
    parse_status: str
    parsed_at: datetime | None
    created_at: datetime
