import uuid

from pydantic import BaseModel


class ClientApprovalWebhookPayload(BaseModel):
    access_request_id: uuid.UUID
    decision: str
    external_reference: str | None = None
