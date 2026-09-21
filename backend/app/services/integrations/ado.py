
from dataclasses import dataclass

from app.config import get_settings
from app.models.user import User

settings = get_settings()


@dataclass
class AdoTask:
    task_id: str
    title: str
    description: str
    project: str
    status: str


_MOCK_TASKS_BY_EMAIL: dict[str, list[AdoTask]] = {
    "khushi.kumari@accessiq.com": [
        AdoTask(
            task_id="ADO-1042",
            title="Grant read access to Billing Service repo",
            description="Khushi needs read access to the Billing Service source repository to review the invoicing module.",
            project="Core Platform",
            status="active",
        ),
    ],
    "rahul.verma@accessiq.com": [
        AdoTask(
            task_id="ADO-1101",
            title="Investigate billing discrepancy",
            description="Rahul is investigating a billing discrepancy reported by finance; needs read and write access to Billing Service data to reproduce and fix it.",
            project="Core Platform",
            status="active",
        ),
    ],
    "pooja.nair@accessiq.com": [
        AdoTask(
            task_id="ADO-1055",
            title="Reporting Portal dashboard refresh",
            description="Update the Reporting Portal dashboards to reflect new billing categories.",
            project="Core Platform",
            status="active",
        ),
    ],
}

_DEFAULT_MOCK_TASKS: list[AdoTask] = [
    AdoTask(
        task_id="ADO-9000",
        title="General platform support",
        description="General support ticket with no specific system access noted.",
        project="Core Platform",
        status="active",
    ),
]


def get_ado_tasks(user: User) -> list[AdoTask]:
    if settings.ado_pat:
        raise NotImplementedError("Real ADO integration ships in M4; ADO_PAT is set but no client is wired up yet.")
    return _MOCK_TASKS_BY_EMAIL.get(user.email, _DEFAULT_MOCK_TASKS)
