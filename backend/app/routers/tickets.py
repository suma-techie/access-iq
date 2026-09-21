import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models.access_request import AccessRequest
from app.models.ticket import Ticket
from app.models.user import User
from app.schemas.ticket import TicketOut, TicketUpdate
from app.services import request_queries

router = APIRouter(tags=["tickets"])

VALID_STATUSES = ("open", "in_progress", "closed", "failed")


@router.get("/requests/{request_id}/tickets", response_model=list[TicketOut])
def list_tickets(
    request_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[Ticket]:
    access_request = db.get(AccessRequest, request_id)
    if access_request is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")
    if not request_queries.can_view_request(db, current_user, access_request):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to view this request")
    return db.query(Ticket).filter(Ticket.access_request_id == request_id).order_by(Ticket.raised_at).all()


@router.patch("/tickets/{ticket_id}", response_model=TicketOut)
def update_ticket(
    ticket_id: uuid.UUID,
    payload: TicketUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Ticket:
    if payload.external_status not in VALID_STATUSES:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"external_status must be one of {VALID_STATUSES}")
    ticket = db.get(Ticket, ticket_id)
    if ticket is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")
    access_request = db.get(AccessRequest, ticket.access_request_id)
    if access_request is None or not request_queries.can_view_request(db, current_user, access_request):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update this ticket")

    ticket.external_status = payload.external_status
    ticket.last_synced_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(ticket)
    return ticket
