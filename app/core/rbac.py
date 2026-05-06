from collections.abc import Callable

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import User
from app.services.auth_service import get_user_from_token

security = HTTPBearer(auto_error=False)


ROLE_PERMISSIONS: dict[str, set[str]] = {
    'Worker': {
        'view_dashboard',
        'view_profile',
        'edit_profile',
        'view_attendance_own',
        'request_attendance_correction',
    },
    'Employee': {
        'view_dashboard',
        'view_profile',
        'edit_profile',
        'view_attendance_own',
        'request_attendance_correction',
        'view_leave_own',
        'request_leave',
        'view_payslip_own',
    },
    'Manager': {
        'view_dashboard',
        'view_profile',
        'edit_profile',
        'view_attendance_own',
        'approve_attendance',
        'approve_leave',
        'view_leave_team',
        'view_payslip_own',
    },
    'HR': {
        'view_dashboard',
        'view_profile',
        'edit_profile',
        'manage_org',
        'view_employee',
        'create_employee',
        'edit_employee',
        'delete_employee',
        'manage_shifts',
        'manage_attendance_records',
        'view_attendance',
        'approve_attendance',
        'view_leave',
        'approve_leave',
        'view_payroll',
        'process_payroll',
        'view_audit_logs',
    },
    'Admin': {
        'view_dashboard',
        'view_profile',
        'edit_profile',
        'manage_org',
        'view_employee',
        'create_employee',
        'edit_employee',
        'delete_employee',
        'manage_shifts',
        'manage_attendance_records',
        'view_attendance',
        'approve_attendance',
        'view_leave',
        'approve_leave',
        'view_payroll',
        'process_payroll',
        'view_audit_logs',
        'manage_roles',
        'manage_settings',
    },
    'Super Admin': {
        '*',
    },
    'CEO': {
        'view_dashboard',
        'view_profile',
        'edit_profile',
        'view_employee',
        'view_attendance',
        'view_leave',
        'view_payroll',
        'view_audit_logs',
    },
}


def _normalize_role(role: str | None) -> str:
    return (role or '').strip()


def get_permissions_for_role(role: str | None) -> set[str]:
    return set(ROLE_PERMISSIONS.get(_normalize_role(role), set()))


def has_permission(role: str | None, permission: str) -> bool:
    permissions = get_permissions_for_role(role)
    return '*' in permissions or permission in permissions


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Not authenticated')
    return get_user_from_token(credentials.credentials, db=db)


def require_permissions(*required_permissions: str) -> Callable[[User], User]:
    def _checker(user: User = Depends(get_current_user)) -> User:
        if not required_permissions:
            return user

        user_permissions = get_permissions_for_role(user.role)
        if '*' in user_permissions:
            return user

        for permission in required_permissions:
            if permission not in user_permissions:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Insufficient privileges')
        return user

    return _checker
