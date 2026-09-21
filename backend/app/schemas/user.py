import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: EmailStr
    display_name: str
    global_role: str
    is_active: bool
    phone_number: str | None
    office_location: str | None
    avatar_url: str | None
    created_at: datetime


class UserCreate(BaseModel):
    email: EmailStr
    display_name: str
    password: str
    global_role: str = "member"


class UserAdminUpdate(BaseModel):

    global_role: str | None = None
    is_active: bool | None = None


class UserSelfUpdate(BaseModel):

    phone_number: str | None = None
    office_location: str | None = None


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str
