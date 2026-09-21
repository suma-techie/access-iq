import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user, require_manager
from app.models.application import Application
from app.models.project import Project
from app.models.user import User
from app.schemas.application import ApplicationCreate, ApplicationOut, ApplicationUpdate

router = APIRouter(prefix="/applications", tags=["applications"])


@router.get("", response_model=list[ApplicationOut])
def list_applications(
    project_id: uuid.UUID | None = None,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> list[Application]:
    query = db.query(Application)
    if project_id is not None:
        query = query.filter(Application.project_id == project_id)
    return query.order_by(Application.name).all()


@router.post("", response_model=ApplicationOut, status_code=status.HTTP_201_CREATED)
def create_application(
    payload: ApplicationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_manager),
) -> Application:
    if db.get(Project, payload.project_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    application = Application(
        project_id=payload.project_id,
        name=payload.name,
        description=payload.description,
        default_requires_client_approval=payload.default_requires_client_approval,
        created_by=current_user.id,
    )
    db.add(application)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="An application with this name already exists") from exc
    db.refresh(application)
    return application


@router.get("/{application_id}", response_model=ApplicationOut)
def get_application(
    application_id: uuid.UUID,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> Application:
    application = db.get(Application, application_id)
    if application is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")
    return application


@router.patch("/{application_id}", response_model=ApplicationOut)
def update_application(
    application_id: uuid.UUID,
    payload: ApplicationUpdate,
    db: Session = Depends(get_db),
    _manager: User = Depends(require_manager),
) -> Application:
    application = db.get(Application, application_id)
    if application is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")
    if payload.name is not None:
        application.name = payload.name
    if payload.description is not None:
        application.description = payload.description
    if payload.default_requires_client_approval is not None:
        application.default_requires_client_approval = payload.default_requires_client_approval
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="An application with this name already exists") from exc
    db.refresh(application)
    return application
