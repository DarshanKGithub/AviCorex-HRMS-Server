"""Service for managing attendance and applying attendance rules."""

from datetime import datetime, date as date_type, timezone, timedelta
import logging
from sqlalchemy import select, func, and_
from sqlalchemy.orm import Session

from app.db.models import Attendance, AttendanceRule, Employee, Shift
from app.schemas.attendance import (
    AttendanceCreate,
    AttendanceUpdate,
    CheckInRequest,
    CheckOutRequest,
    EmployeeAttendanceSummary,
)
from app.services.shift_service import get_employee_current_shift
from fastapi import HTTPException, status


logger = logging.getLogger(__name__)


class AttendanceRuleEngine:
    """Engine for evaluating attendance rules and determining attendance status."""

    def __init__(self, db: Session):
        self.db = db
        self.rules = self._load_rules()

    def _load_rules(self) -> dict[str, AttendanceRule]:
        """Load active attendance rules from database."""
        rules = self.db.query(AttendanceRule).filter(AttendanceRule.is_active.is_(True)).all()
        return {rule.rule_type: rule for rule in rules}

    def calculate_late_minutes(self, check_in_time: datetime, shift: Shift) -> int:
        """Calculate late minutes based on shift start time and grace period."""
        if not shift or not check_in_time:
            return 0

        # Convert check-in time to time only
        check_in_time_only = check_in_time.time()
        shift_start = shift.start_time

        # Calculate minutes late
        check_in_minutes = check_in_time_only.hour * 60 + check_in_time_only.minute
        shift_start_minutes = shift_start.hour * 60 + shift_start.minute

        minutes_late = check_in_minutes - shift_start_minutes
        # Apply grace period
        minutes_late = max(0, minutes_late - shift.grace_period_minutes)

        return minutes_late

    def is_late_entry(self, late_minutes: int) -> bool:
        """Check if entry is considered late based on rules."""
        if 'late_entry' not in self.rules:
            return False
        threshold = self.rules['late_entry'].threshold_minutes
        return late_minutes > threshold

    def calculate_working_hours(self, check_in_time: datetime | None, check_out_time: datetime | None) -> float:
        """Calculate total working hours in decimal format."""
        if not check_in_time or not check_out_time:
            return 0.0
        # Normalize naive/aware datetime mismatches (common with SQLite timezone behavior in tests).
        if check_in_time.tzinfo is None and check_out_time.tzinfo is not None:
            check_in_time = check_in_time.replace(tzinfo=timezone.utc)
        elif check_in_time.tzinfo is not None and check_out_time.tzinfo is None:
            check_out_time = check_out_time.replace(tzinfo=timezone.utc)
        duration = check_out_time - check_in_time
        return duration.total_seconds() / 3600  # Convert to hours

    def is_half_day(self, working_hours: float) -> bool:
        """Check if attendance qualifies as half-day."""
        if 'half_day' not in self.rules:
            return False
        threshold_minutes = self.rules['half_day'].threshold_minutes
        threshold_hours = threshold_minutes / 60
        return working_hours < threshold_hours

    def is_early_exit(self, check_out_time: datetime, shift: Shift) -> bool:
        """Check if employee left early."""
        if not shift or not check_out_time:
            return False

        if 'early_exit' not in self.rules:
            return False

        check_out_time_only = check_out_time.time()
        shift_end = shift.end_time

        # Calculate minutes early
        check_out_minutes = check_out_time_only.hour * 60 + check_out_time_only.minute
        shift_end_minutes = shift_end.hour * 60 + shift_end.minute

        minutes_early = shift_end_minutes - check_out_minutes
        threshold = self.rules['early_exit'].threshold_minutes

        return minutes_early > threshold

    def determine_status(
        self,
        check_in_time: datetime | None,
        check_out_time: datetime | None,
        is_work_from_home: bool,
    ) -> str:
        """Determine attendance status based on check-in/check-out times."""
        if is_work_from_home:
            return 'work-from-home'

        if not check_in_time:
            return 'absent'

        if not check_out_time:
            return 'present'  # Checked in but not checked out (partial day)

        return 'present'


def create_attendance(payload: AttendanceCreate, db: Session) -> Attendance:
    """Create or update attendance record."""
    # Verify employee exists
    employee = db.query(Employee).filter(Employee.id == payload.employee_id).first()
    if not employee:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Employee not found')

    # Check if attendance already exists for this date
    existing = db.query(Attendance).filter(
        and_(
            Attendance.employee_id == payload.employee_id,
            Attendance.attendance_date == payload.attendance_date,
        )
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Attendance record already exists for this date',
        )

    # Initialize rule engine
    rule_engine = AttendanceRuleEngine(db)

    # Get employee's shift for the date
    shift = get_employee_current_shift(payload.employee_id, payload.attendance_date, db)

    # Set default times if not provided
    check_in_time = payload.check_in_time or datetime.now(timezone.utc)
    check_out_time = payload.check_out_time

    # Calculate metrics
    late_minutes = rule_engine.calculate_late_minutes(check_in_time, shift) if check_in_time else 0
    is_late = rule_engine.is_late_entry(late_minutes)

    working_hours = rule_engine.calculate_working_hours(check_in_time, check_out_time)
    is_half_day = rule_engine.is_half_day(working_hours)

    status_value = rule_engine.determine_status(check_in_time, check_out_time, payload.is_work_from_home or False)

    # Create attendance record
    attendance = Attendance(
        employee_id=payload.employee_id,
        attendance_date=payload.attendance_date,
        check_in_time=check_in_time,
        check_out_time=check_out_time,
        status=status_value,
        is_late=is_late,
        late_minutes=late_minutes,
        is_half_day=is_half_day,
        is_work_from_home=payload.is_work_from_home or False,
        notes=payload.notes,
    )
    db.add(attendance)
    db.commit()
    db.refresh(attendance)

    # Write audit log
    _write_attendance_audit_log(db, 'CREATE', attendance)

    return attendance


def get_attendance(attendance_id: str, db: Session) -> Attendance:
    """Retrieve an attendance record by ID."""
    attendance = db.query(Attendance).filter(Attendance.id == attendance_id).first()
    if not attendance:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Attendance record not found')
    return attendance


def check_in(payload: CheckInRequest, db: Session) -> Attendance:
    """Record check-in for an employee."""
    # Verify employee exists
    employee = db.query(Employee).filter(Employee.id == payload.employee_id).first()
    if not employee:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Employee not found')

    # Check if attendance exists for today
    existing = db.query(Attendance).filter(
        and_(
            Attendance.employee_id == payload.employee_id,
            Attendance.attendance_date == payload.attendance_date,
        )
    ).first()

    # Initialize rule engine
    rule_engine = AttendanceRuleEngine(db)

    # Get employee's shift
    shift = get_employee_current_shift(payload.employee_id, payload.attendance_date, db)

    check_in_time = payload.check_in_time or datetime.now(timezone.utc)
    late_minutes = rule_engine.calculate_late_minutes(check_in_time, shift)
    # is_late marks late beyond grace period; separate policy thresholds can be handled elsewhere.
    is_late = late_minutes > 0

    if existing:
        # Update existing record
        existing.check_in_time = check_in_time
        existing.is_late = is_late
        existing.late_minutes = late_minutes
        existing.status = 'present'
        existing.updated_at = datetime.now(timezone.utc)
        db.add(existing)
        db.commit()
        db.refresh(existing)
        if existing.check_in_time and existing.check_in_time.tzinfo is None:
            existing.check_in_time = existing.check_in_time.replace(tzinfo=timezone.utc)
        _write_attendance_audit_log(db, 'UPDATE', existing)
        return existing
    else:
        # Create new record
        attendance = Attendance(
            employee_id=payload.employee_id,
            attendance_date=payload.attendance_date,
            check_in_time=check_in_time,
            status='present',
            is_late=is_late,
            late_minutes=late_minutes,
        )
        db.add(attendance)
        db.commit()
        db.refresh(attendance)
        if attendance.check_in_time and attendance.check_in_time.tzinfo is None:
            attendance.check_in_time = attendance.check_in_time.replace(tzinfo=timezone.utc)
        _write_attendance_audit_log(db, 'CREATE', attendance)
        return attendance


def check_out(payload: CheckOutRequest, db: Session) -> Attendance:
    """Record check-out for an employee."""
    # Get attendance record for today
    attendance = db.query(Attendance).filter(
        and_(
            Attendance.employee_id == payload.employee_id,
            Attendance.attendance_date == payload.attendance_date,
        )
    ).first()

    if not attendance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='No check-in record found for today. Please check-in first.',
        )

    # Initialize rule engine
    rule_engine = AttendanceRuleEngine(db)

    # Get employee's shift
    shift = get_employee_current_shift(payload.employee_id, payload.attendance_date, db)

    check_out_time = payload.check_out_time or datetime.now(timezone.utc)

    # Calculate working hours and half-day status
    working_hours = rule_engine.calculate_working_hours(attendance.check_in_time, check_out_time)
    is_half_day = rule_engine.is_half_day(working_hours)

    # Check for early exit
    is_early_exit = rule_engine.is_early_exit(check_out_time, shift)

    # Update attendance
    attendance.check_out_time = check_out_time
    attendance.is_half_day = is_half_day
    attendance.updated_at = datetime.now(timezone.utc)
    db.add(attendance)
    db.commit()
    db.refresh(attendance)
    if attendance.check_out_time and attendance.check_out_time.tzinfo is None:
        attendance.check_out_time = attendance.check_out_time.replace(tzinfo=timezone.utc)
    if attendance.check_in_time and attendance.check_in_time.tzinfo is None:
        attendance.check_in_time = attendance.check_in_time.replace(tzinfo=timezone.utc)
    _write_attendance_audit_log(db, 'UPDATE', attendance)

    return attendance


def list_attendance(
    db: Session,
    employee_id: str | None = None,
    start_date: date_type | None = None,
    end_date: date_type | None = None,
    page: int = 1,
    size: int = 20,
) -> tuple[list[Attendance], int]:
    """List attendance records with optional filters."""
    query = db.query(Attendance)

    if employee_id:
        query = query.filter(Attendance.employee_id == employee_id)
    if start_date:
        query = query.filter(Attendance.attendance_date >= start_date)
    if end_date:
        query = query.filter(Attendance.attendance_date <= end_date)

    total = query.with_entities(func.count(Attendance.id)).scalar() or 0
    records = query.order_by(Attendance.attendance_date.desc()).offset((page - 1) * size).limit(size).all()

    return records, int(total)


def update_attendance(attendance_id: str, payload: AttendanceUpdate, db: Session) -> Attendance:
    """Update an attendance record."""
    attendance = get_attendance(attendance_id, db)

    # Initialize rule engine for recalculation
    rule_engine = AttendanceRuleEngine(db)

    # Get employee's shift if needed for recalculation
    shift = get_employee_current_shift(attendance.employee_id, attendance.attendance_date, db)

    if payload.check_in_time is not None:
        attendance.check_in_time = payload.check_in_time
        late_minutes = rule_engine.calculate_late_minutes(payload.check_in_time, shift)
        attendance.is_late = rule_engine.is_late_entry(late_minutes)
        attendance.late_minutes = late_minutes

    if payload.check_out_time is not None:
        attendance.check_out_time = payload.check_out_time
        working_hours = rule_engine.calculate_working_hours(attendance.check_in_time, payload.check_out_time)
        attendance.is_half_day = rule_engine.is_half_day(working_hours)

    if payload.status is not None:
        attendance.status = payload.status

    if payload.is_work_from_home is not None:
        attendance.is_work_from_home = payload.is_work_from_home

    if payload.notes is not None:
        attendance.notes = payload.notes

    attendance.updated_at = datetime.now(timezone.utc)
    db.add(attendance)
    db.commit()
    db.refresh(attendance)
    _write_attendance_audit_log(db, 'UPDATE', attendance)

    return attendance


def delete_attendance(attendance_id: str, db: Session) -> Attendance:
    """Delete an attendance record."""
    attendance = get_attendance(attendance_id, db)
    db.delete(attendance)
    db.commit()
    _write_attendance_audit_log(db, 'DELETE', attendance)
    return attendance


def get_employee_attendance_summary(
    employee_id: str,
    start_date: date_type,
    end_date: date_type,
    db: Session,
) -> EmployeeAttendanceSummary:
    """Get attendance summary for an employee within a date range."""
    # Verify employee exists
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Employee not found')

    # Get all attendance records
    records = db.query(Attendance).filter(
        and_(
            Attendance.employee_id == employee_id,
            Attendance.attendance_date >= start_date,
            Attendance.attendance_date <= end_date,
        )
    ).order_by(Attendance.attendance_date).all()

    # Calculate summary
    total_days = (end_date - start_date).days + 1
    present_days = len([r for r in records if r.status == 'present'])
    absent_days = len([r for r in records if r.status == 'absent'])
    half_days = len([r for r in records if r.is_half_day])
    work_from_home_days = len([r for r in records if r.is_work_from_home])
    late_days = len([r for r in records if r.is_late])

    from app.schemas.attendance import AttendanceSummaryItem

    summary_items = [
        AttendanceSummaryItem(
            date=r.attendance_date,
            status=r.status,
            check_in_time=r.check_in_time,
            check_out_time=r.check_out_time,
            is_late=r.is_late,
            is_half_day=r.is_half_day,
            is_work_from_home=r.is_work_from_home,
        )
        for r in records
    ]

    return EmployeeAttendanceSummary(
        employee_id=employee_id,
        start_date=start_date,
        end_date=end_date,
        total_days=total_days,
        present_days=present_days,
        absent_days=absent_days,
        half_days=half_days,
        work_from_home_days=work_from_home_days,
        late_days=late_days,
        records=summary_items,
    )


def _write_attendance_audit_log(db: Session, action: str, attendance: Attendance) -> None:
    """Write attendance operation to audit log."""
    from app.db.models import AuditLog
    import json

    try:
        log = AuditLog(
            actor_id=None,  # Could be set from request context
            action=action,
            object_type='Attendance',
            object_id=attendance.id,
            data=json.dumps({
                'employee_id': attendance.employee_id,
                'attendance_date': attendance.attendance_date.isoformat(),
                'status': attendance.status,
                'is_late': attendance.is_late,
                'is_half_day': attendance.is_half_day,
            }),
        )
        db.add(log)
        db.commit()
    except Exception:
        try:
            db.rollback()
        except Exception:
            pass
        logger.exception('Failed to write attendance audit log for %s %s', action, attendance.id)
