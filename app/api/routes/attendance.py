"""API routes for attendance and shift management."""

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.attendance import (
    ShiftCreate,
    ShiftPublic,
    PaginatedShifts,
    EmployeeShiftAssignmentCreate,
    EmployeeShiftAssignmentPublic,
    PaginatedEmployeeShiftAssignments,
    AttendanceCreate,
    AttendancePublic,
    PaginatedAttendance,
    CheckInRequest,
    CheckOutRequest,
    EmployeeAttendanceSummary,
)
from app.services.shift_service import (
    create_shift,
    get_shift,
    list_shifts,
    assign_shift_to_employee,
    get_employee_shift_assignment,
    list_employee_shift_assignments,
)
from app.services.attendance_service import (
    create_attendance,
    get_attendance,
    check_in,
    check_out,
    list_attendance,
    update_attendance,
    delete_attendance,
    get_employee_attendance_summary,
)
from app.services.auth_service import get_user_from_token

security = HTTPBearer(auto_error=False)
router = APIRouter()


def _attendance_to_dict(a) -> dict:
    return {
        'id': a.id,
        'employee_id': a.employee_id,
        'attendance_date': a.attendance_date,
        'check_in_time': a.check_in_time,
        'check_out_time': a.check_out_time,
        'status': a.status,
        'is_late': a.is_late,
        'late_minutes': a.late_minutes,
        'is_half_day': a.is_half_day,
        'is_work_from_home': a.is_work_from_home,
        'notes': a.notes,
        'created_at': a.created_at,
        'updated_at': a.updated_at,
    }


# ==================== Shift Routes ====================


@router.post('/shifts', response_model=ShiftPublic)
def create_shift_endpoint(
    payload: ShiftCreate,
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: Session = Depends(get_db),
) -> ShiftPublic:
    """Create a new shift (Admin/HR only)."""
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Not authenticated')

    user = get_user_from_token(credentials.credentials, db=db)
    if user.role not in ['Admin', 'HR']:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Insufficient privileges')

    shift = create_shift(payload, db)
    return ShiftPublic.model_validate(shift)


@router.get('/shifts/{shift_id}', response_model=ShiftPublic)
def get_shift_endpoint(
    shift_id: str,
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: Session = Depends(get_db),
) -> ShiftPublic:
    """Retrieve a shift by ID."""
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Not authenticated')

    get_user_from_token(credentials.credentials, db=db)
    shift = get_shift(shift_id, db)
    return ShiftPublic.model_validate(shift)


@router.get('/shifts', response_model=PaginatedShifts)
def list_shifts_endpoint(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: Session = Depends(get_db),
) -> PaginatedShifts:
    """List all shifts with pagination."""
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Not authenticated')

    get_user_from_token(credentials.credentials, db=db)
    shifts, total = list_shifts(db, page=page, size=size)
    return PaginatedShifts(
        items=[ShiftPublic.model_validate(s) for s in shifts],
        total=total,
        page=page,
        size=size,
    )


# ==================== Employee Shift Assignment Routes ====================


@router.post('/employees/{employee_id}/shift-assignment', response_model=EmployeeShiftAssignmentPublic)
def assign_shift_endpoint(
    employee_id: str,
    payload: EmployeeShiftAssignmentCreate,
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: Session = Depends(get_db),
) -> EmployeeShiftAssignmentPublic:
    """Assign a shift to an employee (Admin/HR only)."""
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Not authenticated')

    user = get_user_from_token(credentials.credentials, db=db)
    if user.role not in ['Admin', 'HR']:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Insufficient privileges')

    # Ensure employee_id matches payload
    if payload.employee_id != employee_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Employee ID mismatch')

    assignment = assign_shift_to_employee(payload, db)
    return EmployeeShiftAssignmentPublic.model_validate(assignment)


@router.get('/employees/{employee_id}/shift-assignments', response_model=PaginatedEmployeeShiftAssignments)
def list_employee_shift_assignments_endpoint(
    employee_id: str,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: Session = Depends(get_db),
) -> PaginatedEmployeeShiftAssignments:
    """List shift assignments for an employee."""
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Not authenticated')

    get_user_from_token(credentials.credentials, db=db)
    assignments, total = list_employee_shift_assignments(db, employee_id=employee_id, page=page, size=size)
    return PaginatedEmployeeShiftAssignments(
        items=[EmployeeShiftAssignmentPublic.model_validate(a) for a in assignments],
        total=total,
        page=page,
        size=size,
    )


# ==================== Attendance Routes ====================


@router.post('/check-in', response_model=AttendancePublic)
def check_in_endpoint(
    payload: CheckInRequest,
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: Session = Depends(get_db),
) -> AttendancePublic:
    """Record check-in for an employee."""
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Not authenticated')

    user = get_user_from_token(credentials.credentials, db=db)
    # Allow employees to check in for themselves, and admins/managers for others
    if user.role == 'Employee' and payload.employee_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Cannot check in for other employees')

    attendance = check_in(payload, db)
    return AttendancePublic.model_validate(_attendance_to_dict(attendance))


@router.post('/check-out', response_model=AttendancePublic)
def check_out_endpoint(
    payload: CheckOutRequest,
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: Session = Depends(get_db),
) -> AttendancePublic:
    """Record check-out for an employee."""
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Not authenticated')

    user = get_user_from_token(credentials.credentials, db=db)
    # Allow employees to check out for themselves, and admins/managers for others
    if user.role == 'Employee' and payload.employee_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Cannot check out for other employees')

    attendance = check_out(payload, db)
    return AttendancePublic.model_validate(_attendance_to_dict(attendance))


@router.get('/', response_model=PaginatedAttendance)
def list_attendance_endpoint(
    employee_id: str | None = Query(None),
    start_date: date | None = Query(None),
    end_date: date | None = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: Session = Depends(get_db),
) -> PaginatedAttendance:
    """List attendance records with optional filters."""
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Not authenticated')

    user = get_user_from_token(credentials.credentials, db=db)

    # Employees can only view their own attendance
    if user.role == 'Employee' and employee_id and employee_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Cannot view other employees attendance')

    records, total = list_attendance(db, employee_id=employee_id, start_date=start_date, end_date=end_date, page=page, size=size)
    return PaginatedAttendance(
        items=[AttendancePublic.model_validate(_attendance_to_dict(r)) for r in records],
        total=total,
        page=page,
        size=size,
    )


@router.get('/summary/{employee_id}', response_model=EmployeeAttendanceSummary)
def get_attendance_summary_endpoint(
    employee_id: str,
    start_date: date = Query(...),
    end_date: date = Query(...),
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: Session = Depends(get_db),
) -> EmployeeAttendanceSummary:
    """Get attendance summary for an employee."""
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Not authenticated')

    user = get_user_from_token(credentials.credentials, db=db)

    # Employees can only view their own summary
    if user.role == 'Employee' and employee_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Cannot view other employees attendance')

    if start_date > end_date:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='start_date must be before end_date')

    return get_employee_attendance_summary(employee_id, start_date, end_date, db)


@router.get('/{attendance_id}', response_model=AttendancePublic)
def get_attendance_endpoint(
    attendance_id: str,
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: Session = Depends(get_db),
) -> AttendancePublic:
    """Retrieve an attendance record by ID."""
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Not authenticated')

    get_user_from_token(credentials.credentials, db=db)
    attendance = get_attendance(attendance_id, db)
    return AttendancePublic.model_validate(_attendance_to_dict(attendance))


@router.delete('/{attendance_id}', response_model=AttendancePublic)
def delete_attendance_endpoint(
    attendance_id: str,
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: Session = Depends(get_db),
) -> AttendancePublic:
    """Delete an attendance record (Admin/HR only)."""
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Not authenticated')

    user = get_user_from_token(credentials.credentials, db=db)
    if user.role not in ['Admin', 'HR']:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Insufficient privileges')

    attendance = delete_attendance(attendance_id, db)
    return AttendancePublic.model_validate(_attendance_to_dict(attendance))
