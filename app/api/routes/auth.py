from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.auth import (
    ChangePasswordRequest,
    LoginRequest,
    LoginResponse,
    PasswordChangeResponse,
    ProfileUpdateRequest,
    UserPublic,
)
from app.services.auth_service import (
    authenticate_user,
    change_password,
    create_login_response,
    get_user_from_token,
    to_public_user,
    update_user_profile,
)

router = APIRouter()
security = HTTPBearer(auto_error=False)


@router.post('/login', response_model=LoginResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> LoginResponse:
    user = authenticate_user(email=payload.email, password=payload.password, role=payload.role, db=db)
    return create_login_response(user, db=db)


@router.get('/me', response_model=UserPublic)
def me(credentials: HTTPAuthorizationCredentials | None = Depends(security), db: Session = Depends(get_db)) -> UserPublic:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Not authenticated')

    user = get_user_from_token(credentials.credentials, db=db)
    return to_public_user(user, db=db)


@router.patch('/me', response_model=UserPublic)
def update_me(
    payload: ProfileUpdateRequest,
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: Session = Depends(get_db),
) -> UserPublic:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Not authenticated')

    user = get_user_from_token(credentials.credentials, db=db)
    updated_user = update_user_profile(user, payload.full_name, db=db)
    return to_public_user(updated_user)


@router.post('/change-password', response_model=PasswordChangeResponse)
def change_pwd(
    payload: ChangePasswordRequest,
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: Session = Depends(get_db),
) -> PasswordChangeResponse:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Not authenticated')

    user = get_user_from_token(credentials.credentials, db=db)
    change_password(user, payload.old_password, payload.new_password, db=db)
    return PasswordChangeResponse(message='Password changed successfully')
