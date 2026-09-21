
import uuid
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.models.document import Document
from app.services.text_match import score_overlap, tokenize

MIN_CONFIDENCE = 0.15
MAX_RESULTS = 3


@dataclass
class DocMatch:
    doc_id: uuid.UUID
    filename: str
    chunk_text: str
    confidence: float


def _score(query_tokens: set[str], chunk: str) -> float:
    return score_overlap(query_tokens, chunk)


def search_docs(db: Session, application_id: uuid.UUID, query: str) -> list[DocMatch]:
    documents = (
        db.query(Document)
        .filter(
            Document.application_id == application_id,
            Document.parse_status == "parsed",
            Document.parsed_text.isnot(None),
        )
        .all()
    )
    query_tokens = tokenize(query)
    candidates: list[DocMatch] = []
    for document in documents:
        chunks = [c.strip() for c in (document.parsed_text or "").split("\n\n") if c.strip()]
        for chunk in chunks:
            confidence = _score(query_tokens, chunk)
            if confidence >= MIN_CONFIDENCE:
                candidates.append(
                    DocMatch(
                        doc_id=document.id,
                        filename=document.original_filename,
                        chunk_text=chunk[:1000],
                        confidence=round(confidence, 3),
                    )
                )
    candidates.sort(key=lambda m: m.confidence, reverse=True)
    return candidates[:MAX_RESULTS]
