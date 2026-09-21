import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user, require_manager
from app.models.application import Application
from app.models.application_role import ApplicationRole
from app.models.user import User
from app.schemas.application_role import ApplicationRoleCreate, ApplicationRoleOut, ApplicationRoleUpdate
from app.services.constants import TEAM_ROLE_NAMES

router = APIRouter(prefix="/applications/{application_id}/roles", tags=["application_roles"])

VALID_ROLE_NAMES = TEAM_ROLE_NAMES


@router.get("", response_model=list[ApplicationRoleOut])
def list_application_roles(
    application_id: uuid.UUID,
    include_revoked: bool = False,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> list[ApplicationRole]:
    query = db.query(ApplicationRole).filter(ApplicationRole.application_id == application_id)
    if not include_revoked:
        query = query.filter(ApplicationRole.revoked_at.is_(None))
    return query.order_by(ApplicationRole.assigned_at.desc()).all()


@router.post("", response_model=ApplicationRoleOut, status_code=status.HTTP_201_CREATED)
def assign_application_role(
    application_id: uuid.UUID,
    payload: ApplicationRoleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_manager),
) -> ApplicationRole:
    if payload.role_name not in VALID_ROLE_NAMES:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid role_name")
    if db.get(Application, application_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")
    target_user = db.get(User, payload.user_id)
    if target_user is None or not target_user.is_active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found or inactive")

    role = ApplicationRole(
        application_id=application_id,
        user_id=payload.user_id,
        role_name=payload.role_name,
        assigned_by=current_user.id,
    )
    db.add(role)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User already holds an active assignment of this role on this application",
        ) from exc
    db.refresh(role)
    return role


@router.patch("/{role_id}", response_model=ApplicationRoleOut)
def update_application_role(
    application_id: uuid.UUID,
    role_id: uuid.UUID,
    payload: ApplicationRoleUpdate,
    db: Session = Depends(get_db),
    _manager: User = Depends(require_manager),
) -> ApplicationRole:
    if payload.role_name not in VALID_ROLE_NAMES:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid role_name")
    role = (
        db.query(ApplicationRole)
        .filter(ApplicationRole.id == role_id, ApplicationRole.application_id == application_id, ApplicationRole.revoked_at.is_(None))
        .first()
    )
    if role is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Active role assignment not found")

    role.role_name = payload.role_name
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User already holds an active assignment of this role on this application",
        ) from exc
    db.refresh(role)
    return role


@router.delete("/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
def revoke_application_role(
    application_id: uuid.UUID,
    role_id: uuid.UUID,
    db: Session = Depends(get_db),
    _manager: User = Depends(require_manager),
) -> None:
    role = (
        db.query(ApplicationRole)
        .filter(ApplicationRole.id == role_id, ApplicationRole.application_id == application_id)
        .first()
    )
    if role is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role assignment not found")
    if role.revoked_at is None:
        role.revoked_at = datetime.now(timezone.utc)
        db.commit()
