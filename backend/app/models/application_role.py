import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class ApplicationRole(Base):
    __tablename__ = "application_roles"
    __table_args__ = (
        CheckConstraint(
            "role_name IN ('team_lead', 'application_owner', 'developer', 'qa', 'devops', 'business_analyst', 'support')",
            name="ck_application_roles_role_name",
        ),
        Index(
            "uq_application_roles_active",
            "application_id",
            "user_id",
            "role_name",
            unique=True,
            postgresql_where="revoked_at IS NULL",
        ),
        Index("idx_application_roles_user", "user_id", postgresql_where="revoked_at IS NULL"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    tenant_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    application_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("applications.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    role_name: Mapped[str] = mapped_column(String(30), nullable=False)
    assigned_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    assigned_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
