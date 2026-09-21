import mimetypes
import uuid

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user, require_admin
from app.models.application_role import ApplicationRole
from app.models.user import User
from app.schemas.application_role import ApplicationRoleOut
from app.schemas.user import ChangePasswordRequest, UserAdminUpdate, UserCreate, UserOut, UserSelfUpdate
from app.security import hash_password, verify_password
from app.services.storage import get_storage_backend

router = APIRouter(prefix="/users", tags=["users"])

VALID_GLOBAL_ROLES = ("admin", "manager", "member")


@router.get("", response_model=list[UserOut])
def list_users(
    include_inactive: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[User]:
    query = db.query(User)
    if not (include_inactive and current_user.global_role == "admin"):
        query = query.filter(User.is_active.is_(True))
    return query.order_by(User.display_name).all()


@router.post("", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_user(
    payload: UserCreate,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> User:
    if payload.global_role not in VALID_GLOBAL_ROLES:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid global_role")
    if db.query(User).filter(User.email == payload.email).first() is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    user = User(
        email=payload.email,
        display_name=payload.display_name,
        password_hash=hash_password(payload.password),
        global_role=payload.global_role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.patch("/me", response_model=UserOut)
def update_my_profile(
    payload: UserSelfUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> User:
    if payload.phone_number is not None:
        current_user.phone_number = payload.phone_number
    if payload.office_location is not None:
        current_user.office_location = payload.office_location
    db.commit()
    db.refresh(current_user)
    return current_user


@router.post("/me/avatar", response_model=UserOut)
async def upload_my_avatar(
    file: UploadFile,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> User:
    if file.content_type not in ("image/png", "image/jpeg", "image/webp"):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Avatar must be a PNG, JPEG, or WEBP image")
    content = await file.read()
    if len(content) > 3 * 1024 * 1024:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Avatar must be under 3MB")

    storage = get_storage_backend()
    if current_user.avatar_url:
        try:
            storage.delete(current_user.avatar_url)
        except Exception:
            pass
    storage_url = storage.save(content, file.filename or "avatar")
    current_user.avatar_url = storage_url
    db.commit()
    db.refresh(current_user)
    return current_user


@router.post("/me/change-password", status_code=status.HTTP_204_NO_CONTENT)
def change_my_password(
    payload: ChangePasswordRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    if not verify_password(payload.current_password, current_user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Current password is incorrect")
    if len(payload.new_password) < 8:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="New password must be at least 8 characters")
    current_user.password_hash = hash_password(payload.new_password)
    db.commit()


@router.get("/{user_id}/avatar")
def get_user_avatar(
    user_id: uuid.UUID,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> Response:
    user = db.get(User, user_id)
    if user is None or not user.avatar_url:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No avatar")
    content = get_storage_backend().load(user.avatar_url)
    content_type = mimetypes.guess_type(user.avatar_url)[0] or "application/octet-stream"
    return Response(content=content, media_type=content_type)


@router.patch("/{user_id}", response_model=UserOut)
def admin_update_user(
    user_id: uuid.UUID,
    payload: UserAdminUpdate,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> User:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if payload.global_role is not None:
        if payload.global_role not in VALID_GLOBAL_ROLES:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid global_role")
        user.global_role = payload.global_role
    if payload.is_active is not None:
        user.is_active = payload.is_active
    db.commit()
    db.refresh(user)
    return user


@router.get("/{user_id}/roles", response_model=list[ApplicationRoleOut])
def get_user_roles(
    user_id: uuid.UUID,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> list[ApplicationRole]:
    return (
        db.query(ApplicationRole)
        .filter(ApplicationRole.user_id == user_id)
        .order_by(ApplicationRole.assigned_at.desc())
        .all()
    )
