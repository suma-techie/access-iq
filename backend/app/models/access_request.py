import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base

STATUS_VALUES = (
    "pending",
    "escalated",
    "pending_client_approval",
    "approved",
    "rejected",
    "cannot_verify",
    "revoked",
    "cancelled",
    "expired",
)
SOURCE_TYPE_VALUES = ("ado_task", "doc", "catalog_exact", "none")
RESOLVED_VIA_VALUES = ("auto", "team_lead", "application_owner", "manager", "delegate", "client")


class AccessRequest(Base):
    __tablename__ = "access_requests"
    __table_args__ = (
        CheckConstraint("severity IN ('low', 'medium', 'high')", name="ck_access_requests_severity"),
        CheckConstraint("approval_domain IN ('internal', 'client')", name="ck_access_requests_approval_domain"),
        CheckConstraint(f"status IN {STATUS_VALUES}", name="ck_access_requests_status"),
        CheckConstraint(f"source_type IN {SOURCE_TYPE_VALUES}", name="ck_access_requests_source_type"),
        CheckConstraint(f"resolved_via IN {RESOLVED_VIA_VALUES}", name="ck_access_requests_resolved_via"),
        Index(
            "idx_access_requests_open_by_app",
            "application_id",
            "severity",
            postgresql_where="status IN ('pending', 'escalated')",
        ),
        Index("idx_access_requests_requester", "requester_id"),
        Index("idx_access_requests_status", "status"),
        Index("idx_access_requests_created_at", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    tenant_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    requester_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    application_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("applications.id", ondelete="RESTRICT"), nullable=False
    )
    catalog_entry_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("catalog_entries.id", ondelete="SET NULL"), nullable=True
    )

    requested_text: Mapped[str] = mapped_column(Text, nullable=False)

    severity: Mapped[str | None] = mapped_column(String(10), nullable=True)
    approval_domain: Mapped[str] = mapped_column(String(10), nullable=False)

    status: Mapped[str] = mapped_column(String(25), nullable=False, server_default="pending")

    source_type: Mapped[str] = mapped_column(String(15), nullable=False)
    source_reference: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    ai_rationale: Mapped[str | None] = mapped_column(Text, nullable=True)

    resolved_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    resolved_via: Mapped[str | None] = mapped_column(String(20), nullable=True)
    delegation_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("delegations.id", ondelete="SET NULL"), nullable=True
    )
    resolution_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    revoked_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    revoke_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )
