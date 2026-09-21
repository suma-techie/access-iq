import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, model_validator


class DelegationCreate(BaseModel):
    delegate_id: uuid.UUID
    project_id: uuid.UUID | None = None
    application_id: uuid.UUID | None = None
    end_date: date | None = None

    @model_validator(mode="after")
    def check_exclusive_scope(self) -> "DelegationCreate":
        if self.project_id is not None and self.application_id is not None:
            raise ValueError("project_id and application_id are mutually exclusive (both null = full scope)")
        return self


class DelegationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    delegator_id: uuid.UUID
    delegate_id: uuid.UUID
    project_id: uuid.UUID | None
    application_id: uuid.UUID | None
    start_date: date
    end_date: date | None
    revoked_at: datetime | None
    created_at: datetime
