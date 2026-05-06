from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.rbac import require_permissions
from app.db.database import get_db
from app.db.models import User
from app.schemas.auth import RoleUpdateRequest, UserPublic
from app.schemas.audit import PaginatedAuditLogs, AuditLogPublic
from app.services.audit_service import create_audit_log, list_audit_logs
from app.services.auth_service import to_public_user

router = APIRouter()


@router.get('/audit-logs', response_model=PaginatedAuditLogs)
def audit_logs(page: int = 1, size: int = 20, object_type: str | None = None, actor_id: str | None = None,
               _user: User = Depends(require_permissions('view_audit_logs')), db: Session = Depends(get_db)):

    items, total = list_audit_logs(db=db, page=page, size=size, object_type=object_type, actor_id=actor_id)
    return PaginatedAuditLogs(
        items=[AuditLogPublic(
            id=a.id,
            actor_id=a.actor_id,
            action=a.action,
            object_type=a.object_type,
            object_id=a.object_id,
            data=a.data,
            created_at=a.created_at.isoformat(),
        ) for a in items],
        total=total,
        page=page,
        size=size,
    )


@router.patch('/users/{user_id}/role', response_model=UserPublic)
def update_user_role(
    user_id: str,
    payload: RoleUpdateRequest,
    actor: User = Depends(require_permissions('manage_roles')),
    db: Session = Depends(get_db),
) -> UserPublic:
    allowed_roles = {'Worker', 'Employee', 'Manager', 'HR', 'Admin', 'Super Admin', 'CEO'}
    new_role = payload.role.strip()
    if new_role not in allowed_roles:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Invalid role')

    if actor.id == user_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Cannot change your own role')

    target = db.scalar(select(User).where(User.id == user_id))
    if not target:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='User not found')

    old_role = target.role
    if old_role == new_role:
        return to_public_user(target, db=db)

    # Prevent deleting/demoting last Super Admin.
    if old_role == 'Super Admin' and new_role != 'Super Admin':
        super_admin_count = db.scalar(select(func.count()).select_from(User).where(User.role == 'Super Admin'))
        if int(super_admin_count or 0) <= 1:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Cannot modify last Super Admin')

    target.role = new_role
    create_audit_log(
        db,
        actor_id=actor.id,
        action='ROLE_UPDATED',
        object_type='User',
        object_id=target.id,
        data={
            'old_role': old_role,
            'new_role': new_role,
        },
    )
    db.commit()
    db.refresh(target)
    return to_public_user(target, db=db)
