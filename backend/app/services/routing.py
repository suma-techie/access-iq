
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import update
from sqlalchemy.orm import Session

from app.models.access_request import AccessRequest
from app.models.application import Application
from app.models.catalog import CatalogEntry
from app.models.ticket import Ticket
from app.models.user import User
from app.services.approvers import (
    find_active_delegation,
    find_lead_owner_role,
    resolve_medium_approver_set,
    resolve_org_approvers,
)
from app.services.audit import write_audit
from app.services.constants import EXACT_MATCH_THRESHOLD
from app.services.integrations import servicenow
from app.services.integrations.client_bridge import raise_client_ticket
from app.services.notify import notify_approver, notify_requester


def is_grounded(source_type: str, confidence: float) -> bool:
    if source_type == "catalog_exact":
        return True
    if source_type in ("ado_task", "doc"):
        return confidence >= EXACT_MATCH_THRESHOLD
    return False


def resolve_approval_domain(application: Application, catalog_entry: CatalogEntry | None) -> str:
    if catalog_entry is not None and catalog_entry.requires_client_approval is not None:
        requires_client = catalog_entry.requires_client_approval
    else:
        requires_client = application.default_requires_client_approval
    return "client" if requires_client else "internal"


@dataclass
class ProposalOutcome:
    requested_text: str
    catalog_entry_id: uuid.UUID
    source_type: str
    source_reference: dict
    confidence: float
    ai_rationale: str | None = None


@dataclass
class OutOfScopeOutcome:
    requested_text: str
    ai_rationale: str | None = None


def _notify_all(db: Session, approvers, access_request: AccessRequest, application: Application) -> None:
    user_ids = {a.user_id for a in approvers}
    for user_id in user_ids:
        user = db.get(User, user_id)
        if user:
            notify_approver(user.email, str(access_request.id), application.name)


def apply_proposal_outcome(
    db: Session, requester: User, application: Application, outcome: ProposalOutcome
) -> AccessRequest:
    catalog_entry = db.get(CatalogEntry, outcome.catalog_entry_id)
    if catalog_entry is None:
        raise ValueError(f"catalog_entry_id {outcome.catalog_entry_id} does not exist")

    approval_domain = resolve_approval_domain(application, catalog_entry)
    grounded = is_grounded(outcome.source_type, outcome.confidence)

    access_request = AccessRequest(
        requester_id=requester.id,
        application_id=application.id,
        catalog_entry_id=catalog_entry.id,
        requested_text=outcome.requested_text,
        severity=catalog_entry.severity,
        approval_domain=approval_domain,
        source_type=outcome.source_type,
        source_reference=outcome.source_reference,
        ai_rationale=outcome.ai_rationale,
    )

    if approval_domain == "client":
        access_request.status = "pending_client_approval"
        db.add(access_request)
        db.flush()
        external_id, external_url = raise_client_ticket(str(access_request.id), None)
        db.add(Ticket(access_request_id=access_request.id, ticket_type="client", external_id=external_id, external_url=external_url))
        write_audit(db, actor_type="agent", actor_id=None, action="request_created_client", access_request_id=access_request.id, details={"catalog_entry_id": str(catalog_entry.id)})
        db.commit()
        db.refresh(access_request)
        return access_request

    if not grounded:
        access_request.status = "escalated"
        db.add(access_request)
        db.flush()
        approvers = resolve_org_approvers(db, application.id)
        write_audit(db, actor_type="agent", actor_id=None, action="request_escalated", access_request_id=access_request.id, details={"reason": "ungrounded_weak_candidate", "confidence": outcome.confidence})
        db.commit()
        db.refresh(access_request)
        _notify_all(db, approvers, access_request, application)
        return access_request

    if catalog_entry.severity == "low":
        access_request.status = "approved"
        access_request.resolved_via = "auto"
        access_request.resolved_at = datetime.now(timezone.utc)
        db.add(access_request)
        db.flush()
        external_id, external_url = servicenow.provision_servicenow(str(access_request.id))
        db.add(Ticket(access_request_id=access_request.id, ticket_type="servicenow", external_id=external_id, external_url=external_url))
        write_audit(db, actor_type="agent", actor_id=None, action="auto_approved", access_request_id=access_request.id, details={"source_type": outcome.source_type})
        db.commit()
        db.refresh(access_request)
        return access_request

    access_request.status = "pending"
    db.add(access_request)
    db.flush()
    approvers = resolve_medium_approver_set(db, application.id) if catalog_entry.severity == "medium" else resolve_org_approvers(db, application.id)
    write_audit(db, actor_type="agent", actor_id=None, action="request_pending", access_request_id=access_request.id, details={"severity": catalog_entry.severity})
    db.commit()
    db.refresh(access_request)
    _notify_all(db, approvers, access_request, application)
    return access_request


def apply_out_of_scope_outcome(db: Session, requester: User, application: Application, outcome: OutOfScopeOutcome) -> AccessRequest:
    access_request = AccessRequest(
        requester_id=requester.id,
        application_id=application.id,
        catalog_entry_id=None,
        requested_text=outcome.requested_text,
        severity=None,
        approval_domain=resolve_approval_domain(application, None),
        status="escalated",
        source_type="none",
        source_reference=None,
        ai_rationale=outcome.ai_rationale,
    )
    db.add(access_request)
    db.flush()
    approvers = resolve_org_approvers(db, application.id)
    write_audit(db, actor_type="agent", actor_id=None, action="request_escalated", access_request_id=access_request.id, details={"reason": "out_of_scope"})
    db.commit()
    db.refresh(access_request)
    _notify_all(db, approvers, access_request, application)
    return access_request


def create_cannot_verify_request(db: Session, requester: User, application: Application, requested_text: str) -> AccessRequest:
    access_request = AccessRequest(
        requester_id=requester.id,
        application_id=application.id,
        catalog_entry_id=None,
        requested_text=requested_text,
        severity=None,
        approval_domain=resolve_approval_domain(application, None),
        status="cannot_verify",
        source_type="none",
        source_reference=None,
    )
    db.add(access_request)
    db.flush()
    write_audit(db, actor_type="agent", actor_id=None, action="cannot_verify", access_request_id=access_request.id)
    db.commit()
    db.refresh(access_request)
    return access_request


def request_explicit_review(db: Session, request_id: uuid.UUID, actor: User) -> AccessRequest:
    access_request = db.get(AccessRequest, request_id)
    if access_request is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")
    if access_request.requester_id != actor.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the requester can do this")
    if access_request.status != "cannot_verify":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Only a 'could not verify' request can be escalated this way")

    result = db.execute(
        update(AccessRequest)
        .where(AccessRequest.id == request_id, AccessRequest.status == "cannot_verify")
        .values(status="escalated", source_type="none", updated_at=datetime.now(timezone.utc))
        .returning(AccessRequest.id)
    )
    if result.first() is None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Request is no longer in cannot_verify")
    db.commit()
    db.refresh(access_request)

    application = db.get(Application, access_request.application_id)
    approvers = resolve_org_approvers(db, access_request.application_id)
    write_audit(db, actor_type="user", actor_id=actor.id, action="explicit_review_requested", access_request_id=request_id)
    db.commit()
    if application:
        _notify_all(db, approvers, access_request, application)
    return access_request


def _resolve_actor_capacity(db: Session, access_request: AccessRequest, actor: User) -> tuple[str, uuid.UUID | None]:
    def manager_or_delegate() -> tuple[str, uuid.UUID | None]:
        if actor.global_role in ("manager", "admin"):
            return "manager", None
        delegation = find_active_delegation(db, access_request.application_id, actor.id)
        if delegation is not None:
            return "delegate", delegation.id
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to act on this request")

    if access_request.status == "escalated":
        return manager_or_delegate()
    if access_request.status == "pending" and access_request.severity == "high":
        return manager_or_delegate()
    if access_request.status == "pending" and access_request.severity == "medium":
        role = find_lead_owner_role(db, access_request.application_id, actor.id)
        if role is not None:
            return role.role_name, None
        return manager_or_delegate()
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to act on this request")


def _atomic_transition(db: Session, request_id: uuid.UUID, new_status: str, **values) -> AccessRequest:
    result = db.execute(
        update(AccessRequest)
        .where(AccessRequest.id == request_id, AccessRequest.status.in_(["pending", "escalated"]))
        .values(status=new_status, updated_at=datetime.now(timezone.utc), **values)
        .returning(AccessRequest.id)
    )
    if result.first() is None:
        db.rollback()
        fresh = db.get(AccessRequest, request_id)
        if fresh is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Already resolved (status={fresh.status}, resolved_by={fresh.resolved_by})",
        )
    db.commit()
    access_request = db.get(AccessRequest, request_id)
    if access_request is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")
    return access_request


def approve_request(db: Session, request_id: uuid.UUID, actor: User) -> AccessRequest:
    access_request = db.get(AccessRequest, request_id)
    if access_request is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")
    if access_request.status not in ("pending", "escalated"):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Already resolved (status={access_request.status})")

    resolved_via, delegation_id = _resolve_actor_capacity(db, access_request, actor)
    access_request = _atomic_transition(
        db,
        request_id,
        "approved",
        resolved_by=actor.id,
        resolved_via=resolved_via,
        delegation_id=delegation_id,
        resolved_at=datetime.now(timezone.utc),
    )

    if access_request.approval_domain == "internal" and (access_request.severity in ("medium", "high") or access_request.severity is None):
        external_id, external_url = servicenow.provision_servicenow(str(access_request.id))
        db.add(Ticket(access_request_id=access_request.id, ticket_type="servicenow", external_id=external_id, external_url=external_url))

    write_audit(db, actor_type="user", actor_id=actor.id, action="approved", access_request_id=access_request.id, details={"resolved_via": resolved_via})
    db.commit()
    db.refresh(access_request)

    requester = db.get(User, access_request.requester_id)
    if requester:
        notify_requester(requester.email, str(access_request.id), "approved")
    return access_request


def reject_request(db: Session, request_id: uuid.UUID, actor: User, note: str | None = None) -> AccessRequest:
    access_request = db.get(AccessRequest, request_id)
    if access_request is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")
    if access_request.status not in ("pending", "escalated"):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Already resolved (status={access_request.status})")

    resolved_via, delegation_id = _resolve_actor_capacity(db, access_request, actor)
    access_request = _atomic_transition(
        db,
        request_id,
        "rejected",
        resolved_by=actor.id,
        resolved_via=resolved_via,
        delegation_id=delegation_id,
        resolved_at=datetime.now(timezone.utc),
        resolution_note=note,
    )
    write_audit(db, actor_type="user", actor_id=actor.id, action="rejected", access_request_id=access_request.id, details={"resolved_via": resolved_via, "note": note})
    db.commit()

    requester = db.get(User, access_request.requester_id)
    if requester:
        notify_requester(requester.email, str(access_request.id), "rejected")
    return access_request


TAKE_BACKABLE_STATUSES = ("pending", "escalated", "pending_client_approval")


def cancel_request(db: Session, request_id: uuid.UUID, actor: User) -> AccessRequest:
    access_request = db.get(AccessRequest, request_id)
    if access_request is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")
    if access_request.requester_id != actor.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the requester can take back this request")
    result = db.execute(
        update(AccessRequest)
        .where(AccessRequest.id == request_id, AccessRequest.status.in_(TAKE_BACKABLE_STATUSES))
        .values(status="cancelled", updated_at=datetime.now(timezone.utc))
        .returning(AccessRequest.id)
    )
    if result.first() is None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Request has already been resolved")
    write_audit(db, actor_type="user", actor_id=actor.id, action="cancelled", access_request_id=request_id)
    db.commit()
    return db.get(AccessRequest, request_id)


DELETABLE_STATUSES = ("cannot_verify", "cancelled", "rejected", "expired", "revoked")


def delete_request(db: Session, request_id: uuid.UUID, actor: User) -> None:
    access_request = db.get(AccessRequest, request_id)
    if access_request is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")
    if access_request.status not in DELETABLE_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot delete a request in status '{access_request.status}'",
        )

    is_owner = access_request.requester_id == actor.id
    if access_request.status == "revoked":
        is_admin_manager = actor.global_role in ("manager", "admin")
        is_app_lead_owner = find_lead_owner_role(db, access_request.application_id, actor.id) is not None
        if not (is_owner or is_admin_manager or is_app_lead_owner):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete this record")
    elif not is_owner:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the requester can delete this request")

    db.delete(access_request)
    db.commit()


def revoke_request(db: Session, request_id: uuid.UUID, actor: User, reason: str | None = None) -> AccessRequest:
    access_request = db.get(AccessRequest, request_id)
    if access_request is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")
    if access_request.status != "approved":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Only an approved grant can be revoked")

    is_lead_or_owner = find_lead_owner_role(db, access_request.application_id, actor.id) is not None
    if actor.global_role not in ("manager", "admin") and not is_lead_or_owner:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to revoke this grant")

    result = db.execute(
        update(AccessRequest)
        .where(AccessRequest.id == request_id, AccessRequest.status == "approved")
        .values(
            status="revoked",
            revoked_at=datetime.now(timezone.utc),
            revoked_by=actor.id,
            revoke_reason=reason,
            updated_at=datetime.now(timezone.utc),
        )
        .returning(AccessRequest.id)
    )
    if result.first() is None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Grant is no longer active")

    external_id, external_url = servicenow.provision_servicenow(str(access_request.id))
    db.add(Ticket(access_request_id=access_request.id, ticket_type="servicenow", external_id=external_id, external_url=external_url))
    write_audit(db, actor_type="user", actor_id=actor.id, action="revoked", access_request_id=request_id, details={"reason": reason})
    db.commit()
    return db.get(AccessRequest, request_id)


def record_client_decision(db: Session, request_id: uuid.UUID, actor: User, decision: str, note: str | None) -> AccessRequest:
    access_request = db.get(AccessRequest, request_id)
    if access_request is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")
    if access_request.status != "pending_client_approval":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Request is not awaiting client approval")
    if decision not in ("approved", "rejected"):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="decision must be 'approved' or 'rejected'")

    is_lead_or_owner = find_lead_owner_role(db, access_request.application_id, actor.id) is not None
    if actor.global_role not in ("manager", "admin") and not is_lead_or_owner:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to record this decision")

    result = db.execute(
        update(AccessRequest)
        .where(AccessRequest.id == request_id, AccessRequest.status == "pending_client_approval")
        .values(
            status=decision,
            resolved_by=actor.id,
            resolved_via="client",
            resolution_note=note,
            resolved_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        .returning(AccessRequest.id)
    )
    if result.first() is None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Request is no longer awaiting client approval")

    write_audit(
        db,
        actor_type="user",
        actor_id=actor.id,
        action="client_decision_recorded",
        access_request_id=request_id,
        details={"source": "manual_attestation", "decision": decision, "note": note},
    )
    db.commit()
    return db.get(AccessRequest, request_id)


def record_client_decision_via_webhook(
    db: Session, request_id: uuid.UUID, decision: str, external_reference: str | None
) -> AccessRequest:
    access_request = db.get(AccessRequest, request_id)
    if access_request is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")
    if access_request.status != "pending_client_approval":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Request is not awaiting client approval")
    if decision not in ("approved", "rejected"):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="decision must be 'approved' or 'rejected'")

    result = db.execute(
        update(AccessRequest)
        .where(AccessRequest.id == request_id, AccessRequest.status == "pending_client_approval")
        .values(
            status=decision,
            resolved_via="client",
            resolution_note=f"Recorded via client webhook ({external_reference})" if external_reference else "Recorded via client webhook",
            resolved_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        .returning(AccessRequest.id)
    )
    if result.first() is None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Request is no longer awaiting client approval")

    write_audit(
        db,
        actor_type="system",
        actor_id=None,
        action="client_decision_recorded",
        access_request_id=request_id,
        details={"source": "client_system", "decision": decision, "external_reference": external_reference},
    )
    db.commit()
    return db.get(AccessRequest, request_id)
