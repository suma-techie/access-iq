import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class CatalogCorrection(Base):
    __tablename__ = "catalog_corrections"
    __table_args__ = (
        CheckConstraint("scope IN ('single_request', 'global')", name="ck_catalog_corrections_scope"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    catalog_entry_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("catalog_entries.id", ondelete="CASCADE"), nullable=False
    )
    access_request_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("access_requests.id", ondelete="SET NULL"), nullable=True
    )
    scope: Mapped[str] = mapped_column(String(20), nullable=False, server_default="single_request")
    field_changed: Mapped[str] = mapped_column(String(100), nullable=False)
    old_value: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    new_value: Mapped[dict] = mapped_column(JSONB, nullable=False)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    corrected_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
