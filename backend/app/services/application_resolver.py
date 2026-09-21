
import re
from dataclasses import dataclass
from difflib import SequenceMatcher

from sqlalchemy.orm import Session

from app.models.application import Application

CONFIDENT_THRESHOLD = 0.55
SUGGEST_THRESHOLD = 0.3
CONFIDENT_MARGIN = 0.15


def _normalize(text: str) -> str:
    return re.sub(r"[-_/]+", " ", text.lower()).strip()


def _score(query_norm: str, name_norm: str) -> float:
    if name_norm and name_norm in query_norm:
        return 1.0
    return SequenceMatcher(None, query_norm, name_norm).ratio()


@dataclass
class AppMatch:
    application: Application
    score: float


def resolve_application_from_text(db: Session, text: str) -> tuple[Application | None, list[AppMatch]]:
    applications = db.query(Application).filter(Application.is_active.is_(True)).all()
    if not applications:
        return None, []

    query_norm = _normalize(text)
    scored = sorted(
        (AppMatch(app, _score(query_norm, _normalize(app.name))) for app in applications),
        key=lambda m: m.score,
        reverse=True,
    )

    top = scored[0]
    second = scored[1] if len(scored) > 1 else None

    if top.score >= CONFIDENT_THRESHOLD and (second is None or top.score - second.score >= CONFIDENT_MARGIN):
        return top.application, []

    candidates = [m for m in scored if m.score >= SUGGEST_THRESHOLD][:3]
    return None, candidates
