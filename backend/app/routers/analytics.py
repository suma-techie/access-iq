from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models.access_request import AccessRequest
from app.models.application import Application
from app.models.user import User
from app.services.analytics_scope import scope_condition

router = APIRouter(prefix="/analytics", tags=["analytics"])


def _scoped(db: Session, user: User):
    query = db.query(AccessRequest)
    condition = scope_condition(db, user)
    if condition is not None:
        query = query.filter(condition)
    return query


@router.get("/requests-over-time")
def requests_over_time(
    days: int = 30,
    application_id: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    since = datetime.now(timezone.utc) - timedelta(days=days)
    day = func.date_trunc("day", AccessRequest.created_at)
    query = _scoped(db, current_user).filter(AccessRequest.created_at >= since)
    if application_id:
        query = query.filter(AccessRequest.application_id == application_id)
    rows = query.with_entities(day.label("day"), func.count().label("count")).group_by(day).order_by(day).all()
    return [{"date": r.day.date().isoformat(), "count": r.count} for r in rows]


@router.get("/status-breakdown")
def status_breakdown(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    rows = (
        _scoped(db, current_user)
        .with_entities(AccessRequest.status, func.count().label("count"))
        .group_by(AccessRequest.status)
        .all()
    )
    return [{"status": r.status, "count": r.count} for r in rows]


@router.get("/approval-mode-breakdown")
def approval_mode_breakdown(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    rows = (
        _scoped(db, current_user)
        .filter(AccessRequest.resolved_via.isnot(None))
        .with_entities(AccessRequest.resolved_via, func.count().label("count"))
        .group_by(AccessRequest.resolved_via)
        .all()
    )
    auto = sum(r.count for r in rows if r.resolved_via == "auto")
    manual = sum(r.count for r in rows if r.resolved_via != "auto")
    return {"auto": auto, "manual": manual, "by_resolved_via": [{"resolved_via": r.resolved_via, "count": r.count} for r in rows]}


@router.get("/severity-breakdown")
def severity_breakdown(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    rows = (
        _scoped(db, current_user)
        .with_entities(AccessRequest.severity, func.count().label("count"))
        .group_by(AccessRequest.severity)
        .all()
    )
    order = {"low": 0, "medium": 1, "high": 2, None: 3}
    rows = sorted(rows, key=lambda r: order.get(r.severity, 3))
    return [{"severity": r.severity or "unclassified", "count": r.count} for r in rows]


@router.get("/by-application")
def by_application(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    rows = (
        _scoped(db, current_user)
        .join(Application, Application.id == AccessRequest.application_id)
        .with_entities(Application.name, func.count().label("count"))
        .group_by(Application.name)
        .order_by(func.count().desc())
        .all()
    )
    return [{"application": r.name, "count": r.count} for r in rows]


@router.get("/turnaround-time")
def turnaround_time(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    turnaround_hours = func.extract("epoch", AccessRequest.resolved_at - AccessRequest.created_at) / 3600.0
    query = _scoped(db, current_user).filter(AccessRequest.resolved_at.isnot(None))

    results = {}
    for domain in ("internal", "client"):
        rows = (
            query.filter(AccessRequest.approval_domain == domain)
            .with_entities(
                AccessRequest.severity,
                func.avg(turnaround_hours).label("avg_hours"),
                func.percentile_cont(0.5).within_group(turnaround_hours.asc()).label("median_hours"),
                func.count().label("count"),
            )
            .group_by(AccessRequest.severity)
            .all()
        )
        results[domain] = [
            {
                "severity": r.severity or "unclassified",
                "avg_hours": round(r.avg_hours, 2) if r.avg_hours is not None else None,
                "median_hours": round(r.median_hours, 2) if r.median_hours is not None else None,
                "count": r.count,
            }
            for r in rows
        ]
    return results


@router.get("/summary")
def summary(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    query = _scoped(db, current_user)
    total = query.count()
    pending = query.filter(AccessRequest.status.in_(["pending", "escalated"])).count()
    approved = query.filter(AccessRequest.status == "approved").count()
    rejected = query.filter(AccessRequest.status == "rejected").count()
    awaiting_client = query.filter(AccessRequest.status == "pending_client_approval").count()
    return {
        "total": total,
        "pending": pending,
        "approved": approved,
        "rejected": rejected,
        "awaiting_client": awaiting_client,
    }
