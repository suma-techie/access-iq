
import uuid

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.application_role import ApplicationRole
from app.models.delegation import Delegation
from app.models.user import User
from app.models.access_request import AccessRequest
from app.services.constants import APPROVAL_GRANTING_ROLES


def list_my_requests(db: Session, user: User):
    return db.query(AccessRequest).filter(AccessRequest.requester_id == user.id).order_by(AccessRequest.created_at.desc()).all()


def lead_owner_application_ids(db: Session, user: User) -> set[uuid.UUID]:
    roles = (
        db.query(ApplicationRole)
        .filter(
            ApplicationRole.user_id == user.id,
            ApplicationRole.revoked_at.is_(None),
            ApplicationRole.role_name.in_(APPROVAL_GRANTING_ROLES),
        )
        .all()
    )
    return {r.application_id for r in roles}


def _delegate_application_ids(db: Session, user: User) -> tuple[set[uuid.UUID], bool]:
    delegations = (
        db.query(Delegation)
        .filter(Delegation.delegate_id == user.id, Delegation.revoked_at.is_(None))
        .all()
    )
    from datetime import date

    today = date.today()
    active = [d for d in delegations if d.end_date is None or d.end_date > today]
    app_ids = {d.application_id for d in active if d.application_id is not None}
    has_broader_scope = any(d.application_id is None for d in active)
    return app_ids, has_broader_scope


def list_approval_queue(db: Session, user: User) -> list[AccessRequest]:
    if user.global_role in ("manager", "admin"):
        return (
            db.query(AccessRequest)
            .filter(AccessRequest.status.in_(["pending", "escalated"]))
            .order_by(AccessRequest.created_at.asc())
            .all()
        )

    lead_owner_apps = lead_owner_application_ids(db, user)
    delegate_app_ids, has_broader_scope = _delegate_application_ids(db, user)

    conditions = []
    if lead_owner_apps:
        conditions.append(
            (AccessRequest.status == "pending")
            & (AccessRequest.severity == "medium")
            & (AccessRequest.application_id.in_(lead_owner_apps))
        )
    if delegate_app_ids:
        conditions.append(AccessRequest.application_id.in_(delegate_app_ids) & AccessRequest.status.in_(["pending", "escalated"]))
    if has_broader_scope:
        conditions.append(AccessRequest.status.in_(["pending", "escalated"]))

    if not conditions:
        return []

    return (
        db.query(AccessRequest)
        .filter(AccessRequest.status.in_(["pending", "escalated"]), or_(*conditions))
        .order_by(AccessRequest.created_at.asc())
        .all()
    )


def list_client_queue(db: Session, user: User) -> list[AccessRequest]:
    query = db.query(AccessRequest).filter(AccessRequest.status == "pending_client_approval")
    if user.global_role in ("manager", "admin"):
        return query.order_by(AccessRequest.created_at.asc()).all()
    apps = lead_owner_application_ids(db, user)
    if not apps:
        return []
    return query.filter(AccessRequest.application_id.in_(apps)).order_by(AccessRequest.created_at.asc()).all()


def list_grants(db: Session, application_id: uuid.UUID | None, user_id: uuid.UUID | None) -> list[AccessRequest]:
    query = db.query(AccessRequest).filter(AccessRequest.status.in_(["approved", "revoked"]))
    if application_id is not None:
        query = query.filter(AccessRequest.application_id == application_id)
    if user_id is not None:
        query = query.filter(AccessRequest.requester_id == user_id)
    return query.order_by(AccessRequest.resolved_at.desc()).all()


def can_view_request(db: Session, user: User, access_request: AccessRequest) -> bool:
    if user.global_role in ("manager", "admin"):
        return True
    if access_request.requester_id == user.id:
        return True
    if access_request.application_id in lead_owner_application_ids(db, user):
        return True
    delegate_app_ids, has_broader_scope = _delegate_application_ids(db, user)
    if has_broader_scope or access_request.application_id in delegate_app_ids:
        return True
    return False
