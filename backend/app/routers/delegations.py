import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import require_manager
from app.models.application import Application
from app.models.delegation import Delegation
from app.models.project import Project
from app.models.user import User
from app.schemas.delegation import DelegationCreate, DelegationOut

router = APIRouter(prefix="/delegations", tags=["delegations"])


@router.get("", response_model=list[DelegationOut])
def list_delegations(
    delegator_id: uuid.UUID | None = None,
    delegate_id: uuid.UUID | None = None,
    application_id: uuid.UUID | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_manager),
) -> list[Delegation]:
    query = db.query(Delegation)
    if delegator_id is not None:
        query = query.filter(Delegation.delegator_id == delegator_id)
    if delegate_id is not None:
        query = query.filter(Delegation.delegate_id == delegate_id)
    if application_id is not None:
        query = query.filter(Delegation.application_id == application_id)
    return query.order_by(Delegation.created_at.desc()).all()


@router.post("", response_model=DelegationOut, status_code=status.HTTP_201_CREATED)
def create_delegation(
    payload: DelegationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_manager),
) -> Delegation:
    if payload.project_id is not None and db.get(Project, payload.project_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    if payload.application_id is not None and db.get(Application, payload.application_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")
    delegate = db.get(User, payload.delegate_id)
    if delegate is None or not delegate.is_active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Delegate user not found or inactive")

    delegation = Delegation(
        delegator_id=current_user.id,
        delegate_id=payload.delegate_id,
        project_id=payload.project_id,
        application_id=payload.application_id,
        end_date=payload.end_date,
    )
    db.add(delegation)
    db.commit()
    db.refresh(delegation)
    return delegation


@router.delete("/{delegation_id}", status_code=status.HTTP_204_NO_CONTENT)
def revoke_delegation(
    delegation_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_manager),
) -> None:
    delegation = db.get(Delegation, delegation_id)
    if delegation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Delegation not found")
    if delegation.delegator_id != current_user.id and current_user.global_role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the delegator or an admin can revoke this delegation")
    if delegation.revoked_at is None:
        delegation.revoked_at = datetime.now(timezone.utc)
        db.commit()
