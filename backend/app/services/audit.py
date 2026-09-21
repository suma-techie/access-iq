import uuid
from typing import Any

from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog


def write_audit(
    db: Session,
    *,
    actor_type: str,
    actor_id: uuid.UUID | None,
    action: str,
    access_request_id: uuid.UUID | None = None,
    details: dict[str, Any] | None = None,
) -> None:
    db.add(
        AuditLog(
            access_request_id=access_request_id,
            actor_type=actor_type,
            actor_id=actor_id,
            action=action,
            details=details,
        )
    )
