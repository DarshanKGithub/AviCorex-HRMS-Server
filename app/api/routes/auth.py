from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.orm import Session

from app.core.rbac import get_current_user, get_permissions_for_role, require_permissions
from app.db.database import get_db
from app.db.models import User
from app.schemas.auth import (
    ChangePasswordRequest,
    LoginRequest,
    LoginResponse,
    AvatarDeleteResponse,
    AvatarUploadResponse,
    PermissionsResponse,
    PasswordChangeResponse,
    ProfileUpdateRequest,
    UserPublic,
)
from app.services.auth_service import (
    authenticate_user,
    change_password,
    create_login_response,
    delete_user_avatar,
    save_user_avatar,
    to_public_user,
    update_user_profile,
)
from app.services.audit_service import create_audit_log

router = APIRouter()


@router.post('/login', response_model=LoginResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> LoginResponse:
    user = authenticate_user(email=payload.email, password=payload.password, role=payload.role, db=db)
    return create_login_response(user, db=db)


@router.get('/me', response_model=UserPublic)
def me(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> UserPublic:
    return to_public_user(user, db=db)


@router.get('/me/permissions', response_model=PermissionsResponse)
def me_permissions(user: User = Depends(get_current_user)) -> PermissionsResponse:
    permissions = sorted(get_permissions_for_role(user.role))
    return PermissionsResponse(role=user.role, permissions=permissions)


@router.patch('/me', response_model=UserPublic)
def update_me(
    payload: ProfileUpdateRequest,
    user: User = Depends(require_permissions('edit_profile')),
    db: Session = Depends(get_db),
) -> UserPublic:
    old_full_name = user.full_name
    updated_user = update_user_profile(user, payload.full_name, db=db)
    create_audit_log(
        db,
        actor_id=user.id,
        action='PROFILE_UPDATED',
        object_type='User',
        object_id=user.id,
        data={
            'full_name_old': old_full_name,
            'full_name_new': updated_user.full_name,
        },
    )
    db.commit()
    return to_public_user(updated_user)


@router.post('/me/avatar', response_model=AvatarUploadResponse)
async def upload_me_avatar(
    avatar: UploadFile = File(...),
    user: User = Depends(require_permissions('edit_profile')),
    db: Session = Depends(get_db),
) -> AvatarUploadResponse:
    content = await avatar.read()
    avatar_url = save_user_avatar(user.id, avatar.filename or '', avatar.content_type, content)
    create_audit_log(
        db,
        actor_id=user.id,
        action='PROFILE_AVATAR_UPDATED',
        object_type='User',
        object_id=user.id,
        data={'avatar_url': avatar_url},
    )
    db.commit()
    return AvatarUploadResponse(avatar_url=avatar_url)


@router.delete('/me/avatar', response_model=AvatarDeleteResponse)
def delete_me_avatar(
    user: User = Depends(require_permissions('edit_profile')),
    db: Session = Depends(get_db),
) -> AvatarDeleteResponse:
    delete_user_avatar(user.id)
    create_audit_log(
        db,
        actor_id=user.id,
        action='PROFILE_AVATAR_DELETED',
        object_type='User',
        object_id=user.id,
        data=None,
    )
    db.commit()
    return AvatarDeleteResponse(message='Avatar removed successfully')


@router.post('/change-password', response_model=PasswordChangeResponse)
def change_pwd(
    payload: ChangePasswordRequest,
    user: User = Depends(require_permissions('edit_profile')),
    db: Session = Depends(get_db),
) -> PasswordChangeResponse:
    change_password(user, payload.old_password, payload.new_password, db=db)
    create_audit_log(
        db,
        actor_id=user.id,
        action='PASSWORD_CHANGED',
        object_type='User',
        object_id=user.id,
        data=None,
    )
    db.commit()
    return PasswordChangeResponse(message='Password changed successfully')
