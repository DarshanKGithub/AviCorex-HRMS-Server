from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import create_access_token, verify_password
from app.db.models import User, Employee
from app.schemas.auth import LoginResponse, UserPublic


SEED_USERS = [
    ('Aditi Sharma', 'admin@hrms.com', 'Admin'),
    ('Riya Nair', 'hr@hrms.com', 'HR'),
    ('Arjun Mehta', 'manager@hrms.com', 'Manager'),
    ('Neha Kapoor', 'employee@hrms.com', 'Employee'),
    ('Vikram Rao', 'ceo@hrms.com', 'CEO'),
]


def to_public_user(user: User, db: Session | None = None) -> UserPublic:
    """Return public user payload including optional linked employee_id (if exists)."""
    emp_id: str | None = None
    try:
        if db is not None:
            emp = db.scalar(select(Employee).where(Employee.email == user.email))
            if emp:
                emp_id = emp.id
    except Exception:
        emp_id = None

    return UserPublic(id=user.id, full_name=user.full_name, email=user.email, role=user.role, employee_id=emp_id)


def authenticate_user(*, email: str, password: str, db: Session, role: str | None = None) -> User:
    normalized_email = email.strip().lower()
    user = db.scalar(select(User).where(User.email == normalized_email))
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid email or password')

    if role and user.role.lower() != role.lower():
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Selected role does not match this account')

    if not verify_password(password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid email or password')

    return user


def create_login_response(user: User, db: Session | None = None) -> LoginResponse:
    access_token, expires_at = create_access_token(subject=user.email, user_id=user.id, role=user.role)
    expires_in = int((expires_at - datetime.now(timezone.utc)).total_seconds())
    return LoginResponse(access_token=access_token, expires_in=max(expires_in, 1), user=to_public_user(user, db=db))


def get_user_from_token(token: str, db: Session) -> User:
    payload = decode_token_payload(token)
    subject = payload.get('sub')
    if not subject:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Token missing subject')

    user = db.scalar(select(User).where(User.email == str(subject).lower()))
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='User not found')

    return user


def decode_token_payload(token: str) -> dict:
    try:
        from app.core.security import decode_access_token

        return decode_access_token(token)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc


def update_user_profile(user: User, full_name: str, *, db: Session) -> User:
    user.full_name = full_name.strip()
    db.commit()
    db.refresh(user)
    return user


def change_password(user: User, old_password: str, new_password: str, *, db: Session) -> None:
    from app.core.security import hash_password

    if not verify_password(old_password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Old password is incorrect')

    if old_password == new_password:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='New password must be different from old password')

    user.password_hash = hash_password(new_password)
    db.commit()
