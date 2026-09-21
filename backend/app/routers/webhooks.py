from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.schemas.access_request import AccessRequestOut
from app.schemas.webhook import ClientApprovalWebhookPayload
from app.services.routing import record_client_decision_via_webhook

router = APIRouter(prefix="/webhooks", tags=["webhooks"])
settings = get_settings()


@router.post("/client-approval", response_model=AccessRequestOut)
def client_approval_webhook(
    payload: ClientApprovalWebhookPayload,
    db: Session = Depends(get_db),
    x_webhook_secret: str | None = Header(default=None),
) -> AccessRequestOut:
    if settings.client_webhook_secret and x_webhook_secret != settings.client_webhook_secret:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid webhook secret")

    return record_client_decision_via_webhook(db, payload.access_request_id, payload.decision, payload.external_reference)
