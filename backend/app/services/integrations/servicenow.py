
import secrets

from app.config import get_settings

settings = get_settings()


def _raise_external_ticket() -> str:
    if settings.servicenow_instance_url:
        raise NotImplementedError(
            "Real ServiceNow integration is a fast-follow; SERVICENOW_INSTANCE_URL is set but no client is wired up yet."
        )
    return f"SNOW-{secrets.randbelow(900000) + 100000}"


def provision_servicenow(access_request_id: str) -> tuple[str, str | None]:
    external_id = _raise_external_ticket()
    return external_id, None
