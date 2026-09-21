import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.database import SessionLocal, get_db
from app.deps import get_current_user
from app.models.application import Application
from app.models.application_role import ApplicationRole
from app.models.document import Document
from app.models.user import User
from app.schemas.document import DocumentLinkCreate, DocumentOut
from app.services.document_parser import get_parser
from app.services.storage import get_storage_backend

router = APIRouter(prefix="/applications/{application_id}/documents", tags=["documents"])


def _require_app_access(db: Session, application_id: uuid.UUID, user: User) -> None:
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
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized for this application's documents")


def _parse_document_task(document_id: uuid.UUID) -> None:
    db = SessionLocal()
    try:
        document = db.get(Document, document_id)
        if document is None:
            return
        parser = get_parser(document.file_type)
        if parser is None:
            document.parse_status = "failed"
            db.commit()
            return
        try:
            content = get_storage_backend().load(document.storage_url)
            parsed_text = parser.parse(content)
            document.parsed_text = parsed_text
            document.parse_status = "parsed"
            document.parsed_at = datetime.now(timezone.utc)
        except Exception:
            document.parse_status = "failed"
        db.commit()
    finally:
        db.close()


@router.get("", response_model=list[DocumentOut])
def list_documents(
    application_id: uuid.UUID,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> list[Document]:
    return (
        db.query(Document)
        .filter(Document.application_id == application_id)
        .order_by(Document.created_at.desc())
        .all()
    )


@router.post("", response_model=DocumentOut, status_code=status.HTTP_201_CREATED)
async def upload_document(
    application_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    file: UploadFile,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Document:
    if db.get(Application, application_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")
    _require_app_access(db, application_id, current_user)

    filename = file.filename or "document.pdf"
    if not filename.lower().endswith(".pdf") or file.content_type not in ("application/pdf", "application/octet-stream"):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Only PDF files are accepted at MVP")

    content = await file.read()
    storage_url = get_storage_backend().save(content, filename)

    document = Document(
        application_id=application_id,
        uploaded_by=current_user.id,
        original_filename=filename,
        file_type="pdf",
        storage_url=storage_url,
        parse_status="pending",
    )
    db.add(document)
    db.commit()
    db.refresh(document)

    background_tasks.add_task(_parse_document_task, document.id)
    return document


@router.post("/link", response_model=DocumentOut, status_code=status.HTTP_201_CREATED)
def link_document(
    application_id: uuid.UUID,
    payload: DocumentLinkCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Document:
    if db.get(Application, application_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")
    _require_app_access(db, application_id, current_user)
    if payload.file_type not in ("ado_link", "jira_link"):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="file_type must be 'ado_link' or 'jira_link'")

    document = Document(
        application_id=application_id,
        uploaded_by=current_user.id,
        original_filename=payload.label,
        file_type=payload.file_type,
        storage_url=payload.url,
        parse_status="parsed",
        parsed_text=payload.label,
        parsed_at=datetime.now(timezone.utc),
    )
    db.add(document)
    db.commit()
    db.refresh(document)
    return document


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(
    application_id: uuid.UUID,
    document_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    _require_app_access(db, application_id, current_user)
    document = (
        db.query(Document)
        .filter(Document.id == document_id, Document.application_id == application_id)
        .first()
    )
    if document is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    if document.file_type not in ("ado_link", "jira_link"):
        get_storage_backend().delete(document.storage_url)
    db.delete(document)
    db.commit()
