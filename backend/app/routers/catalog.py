import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models.application import Application
from app.models.application_role import ApplicationRole
from app.models.catalog import CatalogEntry, CatalogEntryVersion
from app.models.user import User
from app.schemas.catalog import CatalogEntryCreate, CatalogEntryOut, CatalogEntryUpdate

router = APIRouter(prefix="/applications/{application_id}/catalog", tags=["catalog"])


def _require_catalog_manager(db: Session, application_id: uuid.UUID, user: User) -> None:
    if user.global_role in ("manager", "admin"):
        return
    has_role = (
        db.query(ApplicationRole)
        .filter(
            ApplicationRole.application_id == application_id,
            ApplicationRole.user_id == user.id,
            ApplicationRole.revoked_at.is_(None),
        )
        .first()
    )
    if has_role is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized for this application's catalog")


@router.get("", response_model=list[CatalogEntryOut])
def list_catalog_entries(
    application_id: uuid.UUID,
    include_inactive: bool = False,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> list[CatalogEntry]:
    query = db.query(CatalogEntry).filter(CatalogEntry.application_id == application_id)
    if not include_inactive:
        query = query.filter(CatalogEntry.is_active.is_(True))
    return query.order_by(CatalogEntry.permission_name).all()


@router.post("", response_model=CatalogEntryOut, status_code=status.HTTP_201_CREATED)
def create_catalog_entry(
    application_id: uuid.UUID,
    payload: CatalogEntryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CatalogEntry:
    if db.get(Application, application_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")
    _require_catalog_manager(db, application_id, current_user)
    if payload.severity not in ("low", "medium", "high"):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid severity")

    entry = CatalogEntry(
        application_id=application_id,
        permission_name=payload.permission_name,
        permission_key=payload.permission_key,
        description=payload.description,
        severity=payload.severity,
        requires_client_approval=payload.requires_client_approval,
        created_by=current_user.id,
    )
    db.add(entry)
    try:
        db.flush()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="permission_key already exists for this application"
        ) from exc

    db.add(
        CatalogEntryVersion(
            catalog_entry_id=entry.id,
            version_no=1,
            snapshot={
                "permission_name": entry.permission_name,
                "permission_key": entry.permission_key,
                "severity": entry.severity,
                "requires_client_approval": entry.requires_client_approval,
                "is_active": entry.is_active,
            },
            change_type="created",
            changed_by=current_user.id,
        )
    )
    db.commit()
    db.refresh(entry)
    return entry


@router.patch("/{entry_id}", response_model=CatalogEntryOut)
def update_catalog_entry(
    application_id: uuid.UUID,
    entry_id: uuid.UUID,
    payload: CatalogEntryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CatalogEntry:
    _require_catalog_manager(db, application_id, current_user)
    entry = (
        db.query(CatalogEntry)
        .filter(CatalogEntry.id == entry_id, CatalogEntry.application_id == application_id)
        .first()
    )
    if entry is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Catalog entry not found")
    if payload.severity is not None and payload.severity not in ("low", "medium", "high"):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid severity")

    if payload.permission_name is not None:
        entry.permission_name = payload.permission_name
    if payload.description is not None:
        entry.description = payload.description
    if payload.severity is not None:
        entry.severity = payload.severity
    if payload.requires_client_approval is not None:
        entry.requires_client_approval = payload.requires_client_approval

    last = (
        db.query(CatalogEntryVersion)
        .filter(CatalogEntryVersion.catalog_entry_id == entry.id)
        .order_by(CatalogEntryVersion.version_no.desc())
        .first()
    )
    db.add(
        CatalogEntryVersion(
            catalog_entry_id=entry.id,
            version_no=(last.version_no + 1 if last else 1),
            snapshot={
                "permission_name": entry.permission_name,
                "permission_key": entry.permission_key,
                "severity": entry.severity,
                "requires_client_approval": entry.requires_client_approval,
                "is_active": entry.is_active,
            },
            change_type="updated",
            changed_by=current_user.id,
        )
    )
    db.commit()
    db.refresh(entry)
    return entry


@router.delete("/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
def deactivate_catalog_entry(
    application_id: uuid.UUID,
    entry_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    _require_catalog_manager(db, application_id, current_user)
    entry = (
        db.query(CatalogEntry)
        .filter(CatalogEntry.id == entry_id, CatalogEntry.application_id == application_id)
        .first()
    )
    if entry is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Catalog entry not found")
    if entry.is_active:
        entry.is_active = False
        last = (
            db.query(CatalogEntryVersion)
            .filter(CatalogEntryVersion.catalog_entry_id == entry.id)
            .order_by(CatalogEntryVersion.version_no.desc())
            .first()
        )
        db.add(
            CatalogEntryVersion(
                catalog_entry_id=entry.id,
                version_no=(last.version_no + 1 if last else 1),
                snapshot={
                    "permission_name": entry.permission_name,
                    "permission_key": entry.permission_key,
                    "severity": entry.severity,
                    "requires_client_approval": entry.requires_client_approval,
                    "is_active": entry.is_active,
                },
                change_type="deactivated",
                changed_by=current_user.id,
            )
        )
        db.commit()
