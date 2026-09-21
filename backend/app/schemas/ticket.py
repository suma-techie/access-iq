import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class TicketOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    access_request_id: uuid.UUID
    ticket_type: str
    external_id: str
    external_status: str
    external_url: str | None
    raised_at: datetime
    last_synced_at: datetime | None


class TicketUpdate(BaseModel):
    external_status: str
