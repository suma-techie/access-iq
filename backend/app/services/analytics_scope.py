from sqlalchemy import or_

from app.models.access_request import AccessRequest
from app.models.user import User
from app.services.request_queries import lead_owner_application_ids


def scope_condition(db, user: User):
    if user.global_role in ("manager", "admin"):
        return None
    apps = lead_owner_application_ids(db, user)
    if apps:
        return or_(AccessRequest.requester_id == user.id, AccessRequest.application_id.in_(apps))
    return AccessRequest.requester_id == user.id
