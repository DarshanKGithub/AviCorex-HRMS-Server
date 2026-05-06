from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import Optional

from app.core.rbac import get_current_user, has_permission, require_permissions
from app.db.database import get_db
from app.db.models import User
from app.schemas.advanced_attendance import (
    AttendanceRegularizationCreate,
    AttendanceRegularizationPublic,
    PaginatedAttendanceRegularizations
)
from app.services.advanced_attendance_service import (
    create_attendance_regularization,
    get_regularizations,
    approve_regularization,
    reject_regularization
)

router = APIRouter()

# --- Regularization Routes ---

@router.post('/regularizations', response_model=AttendanceRegularizationPublic)
def request_regularization(
    payload: AttendanceRegularizationCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Request attendance regularization."""
    if payload.employee_id != user.id and not has_permission(user.role, 'manage_attendance'):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot request for other employees")
    
    reg = create_attendance_regularization(payload, db)
    return AttendanceRegularizationPublic.model_validate(reg)


@router.get('/regularizations', response_model=PaginatedAttendanceRegularizations)
def list_regularizations(
    employee_id: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List regularizations."""
    if employee_id and employee_id != user.id and not has_permission(user.role, 'view_attendance'):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot view other employees regularizations")

    if not employee_id and not has_permission(user.role, 'view_attendance'):
        employee_id = user.id

    items, total = get_regularizations(db, employee_id, status_filter, page, size)
    
    return PaginatedAttendanceRegularizations(
        items=[AttendanceRegularizationPublic.model_validate(i) for i in items],
        total=total,
        page=page,
        size=size
    )


@router.post('/regularizations/{reg_id}/approve', response_model=AttendanceRegularizationPublic)
def approve_regularization_endpoint(
    reg_id: str,
    user: User = Depends(require_permissions('approve_attendance')),
    db: Session = Depends(get_db)
):
    """Approve a regularization request."""
    reg = approve_regularization(reg_id, user.id, db)
    return AttendanceRegularizationPublic.model_validate(reg)


@router.post('/regularizations/{reg_id}/reject', response_model=AttendanceRegularizationPublic)
def reject_regularization_endpoint(
    reg_id: str,
    user: User = Depends(require_permissions('approve_attendance')),
    db: Session = Depends(get_db)
):
    """Reject a regularization request."""
    reg = reject_regularization(reg_id, user.id, db)
    return AttendanceRegularizationPublic.model_validate(reg)
