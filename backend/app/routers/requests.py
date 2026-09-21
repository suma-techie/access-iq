import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models.access_request import AccessRequest
from app.models.application import Application
from app.models.user import User
from app.schemas.access_request import (
    AccessRequestOut,
    ClientStatusPayload,
    RejectPayload,
    RevokePayload,
)
from app.schemas.chat import ChatRequest, ChatResponse
from app.services import request_queries, routing
from app.services.agent import run_agent
from app.services.application_resolver import resolve_application_from_text

router = APIRouter(tags=["requests"])


@router.post("/chat", response_model=ChatResponse)
def chat(
    payload: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ChatResponse:
    history = [{"role": m.role, "content": m.content} for m in payload.messages]

    application: Application | None = None
    if payload.application_id is not None:
        application = db.get(Application, payload.application_id)
        if application is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")
    else:
        last_user_message = next((m["content"] for m in reversed(history) if m["role"] == "user"), "")
        confident, candidates = resolve_application_from_text(db, last_user_message)
        if confident is not None:
            application = confident
        elif candidates:
            names = ", ".join(c.application.name for c in candidates)
            suffix = "?" if len(candidates) == 1 else " — which one?"
            return ChatResponse(reply=f"Did you mean {names}{suffix}")
        else:
            return ChatResponse(reply="Which application is this for? (e.g. \"Billing Service\")")

    result = run_agent(db, current_user, application, history)
    return ChatResponse(
        reply=result.reply,
        created_requests=result.created_requests,
        resolved_application_id=application.id,
        resolved_application_name=application.name,
    )


@router.get("/requests", response_model=list[AccessRequestOut])
def list_requests(
    scope: str = "mine",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[AccessRequest]:
    if scope == "mine":
        return request_queries.list_my_requests(db, current_user)
    if scope == "approvals":
        return request_queries.list_approval_queue(db, current_user)
    if scope == "client":
        return request_queries.list_client_queue(db, current_user)
    raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="scope must be 'mine', 'approvals', or 'client'")


@router.get("/grants", response_model=list[AccessRequestOut])
def list_grants(
    application_id: uuid.UUID | None = None,
    user_id: uuid.UUID | None = None,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> list[AccessRequest]:
    return request_queries.list_grants(db, application_id, user_id)


@router.get("/requests/{request_id}", response_model=AccessRequestOut)
def get_request(
    request_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AccessRequest:
    access_request = db.get(AccessRequest, request_id)
    if access_request is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")
    if not request_queries.can_view_request(db, current_user, access_request):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to view this request")
    return access_request


@router.post("/requests/{request_id}/approve", response_model=AccessRequestOut)
def approve(
    request_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AccessRequest:
    return routing.approve_request(db, request_id, current_user)


@router.post("/requests/{request_id}/reject", response_model=AccessRequestOut)
def reject(
    request_id: uuid.UUID,
    payload: RejectPayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AccessRequest:
    return routing.reject_request(db, request_id, current_user, payload.note)


@router.post("/requests/{request_id}/cancel", response_model=AccessRequestOut)
def cancel(
    request_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AccessRequest:
    return routing.cancel_request(db, request_id, current_user)


@router.delete("/requests/{request_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_my_request(
    request_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    routing.delete_request(db, request_id, current_user)


@router.post("/requests/{request_id}/request-review", response_model=AccessRequestOut)
def request_review(
    request_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AccessRequest:
    return routing.request_explicit_review(db, request_id, current_user)


@router.post("/requests/{request_id}/revoke", response_model=AccessRequestOut)
def revoke(
    request_id: uuid.UUID,
    payload: RevokePayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AccessRequest:
    return routing.revoke_request(db, request_id, current_user, payload.reason)


@router.post("/requests/{request_id}/client-status", response_model=AccessRequestOut)
def client_status(
    request_id: uuid.UUID,
    payload: ClientStatusPayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AccessRequest:
    return routing.record_client_decision(db, request_id, current_user, payload.decision, payload.note)
