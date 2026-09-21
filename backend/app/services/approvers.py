
import uuid
from dataclasses import dataclass
from datetime import date

from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from app.models.application import Application
from app.models.application_role import ApplicationRole
from app.models.delegation import Delegation
from app.models.user import User
from app.services.constants import APPROVAL_GRANTING_ROLES


@dataclass
class Approver:
    user_id: uuid.UUID
    via: str
    delegation_id: uuid.UUID | None = None


def _active_delegations_for(db: Session, application_id: uuid.UUID) -> list[Delegation]:
    application = db.get(Application, application_id)
    if application is None:
        return []
    today = date.today()
    return (
        db.query(Delegation)
        .filter(
            Delegation.revoked_at.is_(None),
            or_(Delegation.end_date.is_(None), Delegation.end_date > today),
            or_(
                Delegation.application_id == application_id,
                and_(Delegation.application_id.is_(None), Delegation.project_id.is_(None)),
                Delegation.project_id == application.project_id,
            ),
        )
        .all()
    )


def get_active_delegates(db: Session, application_id: uuid.UUID) -> list[Delegation]:
    return _active_delegations_for(db, application_id)


def resolve_org_approvers(db: Session, application_id: uuid.UUID) -> list[Approver]:
    managers = db.query(User).filter(User.global_role == "manager", User.is_active.is_(True)).all()
    approvers = [Approver(user_id=m.id, via="manager") for m in managers]
    manager_ids = {m.id for m in managers}
    for delegation in _active_delegations_for(db, application_id):
        if delegation.delegate_id not in manager_ids:
            approvers.append(Approver(user_id=delegation.delegate_id, via="delegate", delegation_id=delegation.id))
    return approvers


def resolve_lead_owner_approvers(db: Session, application_id: uuid.UUID) -> list[Approver]:
    roles = (
        db.query(ApplicationRole)
        .filter(
            ApplicationRole.application_id == application_id,
            ApplicationRole.revoked_at.is_(None),
            ApplicationRole.role_name.in_(APPROVAL_GRANTING_ROLES),
        )
        .all()
    )
    return [Approver(user_id=r.user_id, via=r.role_name) for r in roles]


def resolve_medium_approver_set(db: Session, application_id: uuid.UUID) -> list[Approver]:
    seen: set[uuid.UUID] = set()
    result: list[Approver] = []
    for approver in resolve_lead_owner_approvers(db, application_id) + resolve_org_approvers(db, application_id):
        if approver.user_id not in seen:
            seen.add(approver.user_id)
            result.append(approver)
    return result


def find_lead_owner_role(db: Session, application_id: uuid.UUID, user_id: uuid.UUID) -> ApplicationRole | None:
    return (
        db.query(ApplicationRole)
        .filter(
            ApplicationRole.application_id == application_id,
            ApplicationRole.user_id == user_id,
            ApplicationRole.revoked_at.is_(None),
            ApplicationRole.role_name.in_(APPROVAL_GRANTING_ROLES),
        )
        .first()
    )


def find_active_delegation(db: Session, application_id: uuid.UUID, user_id: uuid.UUID) -> Delegation | None:
    for delegation in _active_delegations_for(db, application_id):
        if delegation.delegate_id == user_id:
            return delegation
    return None
