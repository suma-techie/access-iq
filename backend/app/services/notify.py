
import logging

logger = logging.getLogger("accessiq.notify")


def _deliver(to_email: str, subject: str, body: str) -> None:
    logger.info("STUB EMAIL to=%s subject=%r body=%r", to_email, subject, body)


def notify_approver(approver_email: str, access_request_id: str, application_name: str) -> None:
    _deliver(
        to_email=approver_email,
        subject=f"AccessIQ: approval needed ({application_name})",
        body=f"Request {access_request_id} on {application_name} needs your review.",
    )


def notify_requester(requester_email: str, access_request_id: str, status: str) -> None:
    _deliver(
        to_email=requester_email,
        subject=f"AccessIQ: request {status}",
        body=f"Your request {access_request_id} is now {status}.",
    )
