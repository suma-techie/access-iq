import uuid

from pydantic import BaseModel

from app.schemas.access_request import AccessRequestOut


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    application_id: uuid.UUID | None = None
    messages: list[ChatMessage]


class ChatResponse(BaseModel):
    reply: str
    created_requests: list[AccessRequestOut] = []
    resolved_application_id: uuid.UUID | None = None
    resolved_application_name: str | None = None
