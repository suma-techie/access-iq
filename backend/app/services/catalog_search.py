
import uuid
from dataclasses import dataclass

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.catalog import CatalogEntry
from app.services.constants import EXACT_MATCH_THRESHOLD

CATALOG_EXACT_THRESHOLD = EXACT_MATCH_THRESHOLD
CATALOG_MIN_THRESHOLD = 0.2
MAX_RESULTS = 5


@dataclass
class CatalogMatch:
    catalog_entry_id: uuid.UUID
    application_id: uuid.UUID
    permission_name: str
    permission_key: str
    severity: str
    requires_client_approval: bool | None
    confidence: float
    matched_alias: str


def search_catalog(db: Session, application_id: uuid.UUID, query: str) -> list[CatalogMatch]:
    similarity = func.greatest(
        func.similarity(CatalogEntry.permission_name, query),
        func.similarity(CatalogEntry.permission_key, query),
    )
    rows = (
        db.query(CatalogEntry, similarity.label("confidence"))
        .filter(
            CatalogEntry.application_id == application_id,
            CatalogEntry.is_active.is_(True),
            similarity >= CATALOG_MIN_THRESHOLD,
        )
        .order_by(similarity.desc())
        .limit(MAX_RESULTS)
        .all()
    )
    return [
        CatalogMatch(
            catalog_entry_id=entry.id,
            application_id=entry.application_id,
            permission_name=entry.permission_name,
            permission_key=entry.permission_key,
            severity=entry.severity,
            requires_client_approval=entry.requires_client_approval,
            confidence=round(float(confidence), 3),
            matched_alias=entry.permission_name,
        )
        for entry, confidence in rows
    ]
