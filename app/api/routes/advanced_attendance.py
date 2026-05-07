from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import Optional

from app.core.rbac import get_current_user, has_permission, require_permissions
from app.db.database import get_db
from app.db.models import User
from app.schemas.advanced_attendance import (
    AttendanceRegularizationCreate,
    AttendanceRegularizationPublic,
    PaginatedAttendanceRegularizations,
    TimesheetCreate,
    TimesheetPublic,
    PaginatedTimesheets,
    OvertimeRequestCreate,
    OvertimeRequestPublic,
    PaginatedOvertimeRequests,
    CompOffRequestCreate,
    CompOffRequestPublic,
    PaginatedCompOffRequests,
)
from app.services.advanced_attendance_service import (
    create_attendance_regularization,
    get_regularizations,
    approve_regularization,
    reject_regularization,
    create_timesheet,
    get_timesheets,
    update_timesheet,
    create_overtime_request,
    get_overtime_requests,
    approve_overtime,
    reject_overtime,
    create_comp_off_request,
    get_comp_off_requests,
    approve_comp_off,
    reject_comp_off,
)

router = APIRouter()

# --- Timesheet Routes ---

@router.post('/timesheets', response_model=TimesheetPublic)
def create_timesheet_endpoint(
    payload: TimesheetCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a timesheet entry."""
    if payload.employee_id != user.id and not has_permission(user.role, 'manage_attendance'):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot create timesheet for other employees")
    
    ts = create_timesheet(payload, db)
    return TimesheetPublic.model_validate(ts)


@router.get('/timesheets', response_model=PaginatedTimesheets)
def list_timesheets(
    employee_id: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List timesheets."""
    if employee_id and employee_id != user.id and not has_permission(user.role, 'view_attendance'):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot view other employees timesheets")

    if not employee_id and not has_permission(user.role, 'view_attendance'):
        employee_id = user.id

    items, total = get_timesheets(db, employee_id, status_filter, page, size)
    
    return PaginatedTimesheets(
        items=[TimesheetPublic.model_validate(i) for i in items],
        total=total,
        page=page,
        size=size
    )


@router.put('/timesheets/{ts_id}', response_model=TimesheetPublic)
def update_timesheet_endpoint(
    ts_id: str,
    payload: TimesheetCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a timesheet entry (only Draft status)."""
    ts = update_timesheet(ts_id, payload, user.id, db)
    return TimesheetPublic.model_validate(ts)


# --- Overtime Request Routes ---

@router.post('/overtime-requests', response_model=OvertimeRequestPublic)
def create_overtime_endpoint(
    payload: OvertimeRequestCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create an overtime request."""
    if payload.employee_id != user.id and not has_permission(user.role, 'manage_attendance'):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot create overtime for other employees")
    
    ot = create_overtime_request(payload, db)
    return OvertimeRequestPublic.model_validate(ot)


@router.get('/overtime-requests', response_model=PaginatedOvertimeRequests)
def list_overtime(
    employee_id: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List overtime requests."""
    if employee_id and employee_id != user.id and not has_permission(user.role, 'view_attendance'):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot view other employees overtime")

    if not employee_id and not has_permission(user.role, 'view_attendance'):
        employee_id = user.id

    items, total = get_overtime_requests(db, employee_id, status_filter, page, size)
    
    return PaginatedOvertimeRequests(
        items=[OvertimeRequestPublic.model_validate(i) for i in items],
        total=total,
        page=page,
        size=size
    )


@router.post('/overtime-requests/{ot_id}/approve', response_model=OvertimeRequestPublic)
def approve_overtime_endpoint(
    ot_id: str,
    user: User = Depends(require_permissions('approve_attendance')),
    db: Session = Depends(get_db)
):
    """Approve an overtime request."""
    ot = approve_overtime(ot_id, user.id, db)
    return OvertimeRequestPublic.model_validate(ot)


@router.post('/overtime-requests/{ot_id}/reject', response_model=OvertimeRequestPublic)
def reject_overtime_endpoint(
    ot_id: str,
    user: User = Depends(require_permissions('approve_attendance')),
    db: Session = Depends(get_db)
):
    """Reject an overtime request."""
    ot = reject_overtime(ot_id, user.id, db)
    return OvertimeRequestPublic.model_validate(ot)


# --- Comp-Off Request Routes ---

@router.post('/comp-off-requests', response_model=CompOffRequestPublic)
def create_comp_off_endpoint(
    payload: CompOffRequestCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a comp-off request."""
    if payload.employee_id != user.id and not has_permission(user.role, 'manage_attendance'):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot create comp-off for other employees")
    
    co = create_comp_off_request(payload, db)
    return CompOffRequestPublic.model_validate(co)


@router.get('/comp-off-requests', response_model=PaginatedCompOffRequests)
def list_comp_off(
    employee_id: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List comp-off requests."""
    if employee_id and employee_id != user.id and not has_permission(user.role, 'view_attendance'):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot view other employees comp-off")

    if not employee_id and not has_permission(user.role, 'view_attendance'):
        employee_id = user.id

    items, total = get_comp_off_requests(db, employee_id, status_filter, page, size)
    
    return PaginatedCompOffRequests(
        items=[CompOffRequestPublic.model_validate(i) for i in items],
        total=total,
        page=page,
        size=size
    )


@router.post('/comp-off-requests/{co_id}/approve', response_model=CompOffRequestPublic)
def approve_comp_off_endpoint(
    co_id: str,
    user: User = Depends(require_permissions('approve_attendance')),
    db: Session = Depends(get_db)
):
    """Approve a comp-off request."""
    co = approve_comp_off(co_id, user.id, db)
    return CompOffRequestPublic.model_validate(co)


@router.post('/comp-off-requests/{co_id}/reject', response_model=CompOffRequestPublic)
def reject_comp_off_endpoint(
    co_id: str,
    user: User = Depends(require_permissions('approve_attendance')),
    db: Session = Depends(get_db)
):
    """Reject a comp-off request."""
    co = reject_comp_off(co_id, user.id, db)
    return CompOffRequestPublic.model_validate(co)


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
