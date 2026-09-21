
import secrets


def raise_client_ticket(access_request_id: str, client_system_ref: str | None) -> tuple[str, str | None]:
    external_id = f"CLIENT-{secrets.randbelow(900000) + 100000}"
    return external_id, None
