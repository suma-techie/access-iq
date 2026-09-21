import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class AccessRequestOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    requester_id: uuid.UUID
    application_id: uuid.UUID
    catalog_entry_id: uuid.UUID | None
    requested_text: str
    severity: str | None
    approval_domain: str
    status: str
    source_type: str
    source_reference: dict[str, Any] | None
    ai_rationale: str | None
    resolved_by: uuid.UUID | None
    resolved_via: str | None
    delegation_id: uuid.UUID | None
    resolution_note: str | None
    resolved_at: datetime | None
    expires_at: datetime | None
    revoked_at: datetime | None
    revoked_by: uuid.UUID | None
    revoke_reason: str | None
    created_at: datetime
    updated_at: datetime


class RejectPayload(BaseModel):
    note: str | None = None


class RevokePayload(BaseModel):
    reason: str | None = None


class ClientStatusPayload(BaseModel):
    decision: str
    note: str | None = None
