import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Ticket(Base):
    __tablename__ = "tickets"
    __table_args__ = (
        CheckConstraint("ticket_type IN ('servicenow', 'client')", name="ck_tickets_ticket_type"),
        CheckConstraint(
            "external_status IN ('open', 'in_progress', 'closed', 'failed')", name="ck_tickets_external_status"
        ),
        Index("idx_tickets_request", "access_request_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    access_request_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("access_requests.id", ondelete="CASCADE"), nullable=False
    )
    ticket_type: Mapped[str] = mapped_column(String(15), nullable=False)
    external_id: Mapped[str] = mapped_column(String(255), nullable=False)
    external_status: Mapped[str] = mapped_column(String(20), nullable=False, server_default="open")
    external_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    raised_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
