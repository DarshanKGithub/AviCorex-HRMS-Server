"""Unit tests for attendance services and rule engine."""

import pytest
from datetime import date, datetime, time, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.database import Base
from app.db.models import Employee, Shift, EmployeeShiftAssignment, Attendance, AttendanceRule
from app.services.attendance_service import (
    AttendanceRuleEngine,
    create_attendance,
    check_in,
    check_out,
    get_employee_attendance_summary,
)
from app.services.shift_service import assign_shift_to_employee
from app.schemas.attendance import (
    AttendanceCreate,
    CheckInRequest,
    CheckOutRequest,
    ShiftCreate,
    EmployeeShiftAssignmentCreate,
)


@pytest.fixture()
def db_session():
    """Create an in-memory SQLite test database."""
    engine = create_engine('sqlite:///:memory:', future=True)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
    session = Session()
    
    # Seed default rules
    rules = [
        AttendanceRule(name="Late Entry After 30 Minutes", rule_type="late_entry", threshold_minutes=30),
        AttendanceRule(name="Half Day Below 4 Hours", rule_type="half_day", threshold_minutes=240),
        AttendanceRule(name="Early Exit More Than 30 Minutes", rule_type="early_exit", threshold_minutes=30),
    ]
    for rule in rules:
        session.add(rule)
    session.commit()
    
    try:
        yield session
    finally:
        session.close()


# ==================== Attendance Rule Engine Tests ====================


def test_rule_engine_initialization(db_session):
    """Test that rule engine loads rules correctly."""
    engine = AttendanceRuleEngine(db_session)
    assert 'late_entry' in engine.rules
    assert 'half_day' in engine.rules
    assert 'early_exit' in engine.rules


def test_calculate_late_minutes_within_grace_period(db_session):
    """Test late calculation with grace period."""
    engine = AttendanceRuleEngine(db_session)
    
    shift = Shift(
        name='Morning',
        start_time=time(9, 0),
        end_time=time(18, 0),
        grace_period_minutes=5,
    )
    db_session.add(shift)
    db_session.commit()
    db_session.refresh(shift)
    
    # Check in 3 minutes late (within grace period)
    check_in_time = datetime(2024, 5, 1, 9, 3, tzinfo=timezone.utc)
    late_minutes = engine.calculate_late_minutes(check_in_time, shift)
    
    assert late_minutes == 0  # Still within grace period


def test_calculate_late_minutes_beyond_grace_period(db_session):
    """Test late calculation beyond grace period."""
    engine = AttendanceRuleEngine(db_session)
    
    shift = Shift(
        name='Morning',
        start_time=time(9, 0),
        end_time=time(18, 0),
        grace_period_minutes=5,
    )
    db_session.add(shift)
    db_session.commit()
    db_session.refresh(shift)
    
    # Check in 40 minutes late
    check_in_time = datetime(2024, 5, 1, 9, 40, tzinfo=timezone.utc)
    late_minutes = engine.calculate_late_minutes(check_in_time, shift)
    
    assert late_minutes == 35  # 40 - 5 grace = 35


def test_is_late_entry_threshold(db_session):
    """Test late entry threshold determination."""
    engine = AttendanceRuleEngine(db_session)
    
    # Below threshold
    assert not engine.is_late_entry(15)
    
    # At threshold
    assert not engine.is_late_entry(30)
    
    # Above threshold
    assert engine.is_late_entry(31)


def test_calculate_working_hours(db_session):
    """Test working hours calculation."""
    engine = AttendanceRuleEngine(db_session)
    
    check_in = datetime(2024, 5, 1, 9, 0, tzinfo=timezone.utc)
    check_out = datetime(2024, 5, 1, 17, 0, tzinfo=timezone.utc)
    
    hours = engine.calculate_working_hours(check_in, check_out)
    assert hours == 8.0


def test_calculate_partial_working_hours(db_session):
    """Test partial working hours calculation."""
    engine = AttendanceRuleEngine(db_session)
    
    check_in = datetime(2024, 5, 1, 9, 0, tzinfo=timezone.utc)
    check_out = datetime(2024, 5, 1, 13, 30, tzinfo=timezone.utc)  # 4.5 hours
    
    hours = engine.calculate_working_hours(check_in, check_out)
    assert hours == 4.5


def test_is_half_day_threshold(db_session):
    """Test half-day threshold determination (below 4 hours)."""
    engine = AttendanceRuleEngine(db_session)
    
    # 3.5 hours (below threshold)
    assert engine.is_half_day(3.5)
    
    # 4 hours (at threshold)
    assert not engine.is_half_day(4.0)
    
    # 4.5 hours (above threshold)
    assert not engine.is_half_day(4.5)


def test_determine_status_absent(db_session):
    """Test status determination for absent."""
    engine = AttendanceRuleEngine(db_session)
    
    status = engine.determine_status(None, None, False)
    assert status == 'absent'


def test_determine_status_present(db_session):
    """Test status determination for present."""
    engine = AttendanceRuleEngine(db_session)
    
    check_in = datetime(2024, 5, 1, 9, 0, tzinfo=timezone.utc)
    check_out = datetime(2024, 5, 1, 17, 0, tzinfo=timezone.utc)
    
    status = engine.determine_status(check_in, check_out, False)
    assert status == 'present'


def test_determine_status_work_from_home(db_session):
    """Test status determination for work from home."""
    engine = AttendanceRuleEngine(db_session)
    
    status = engine.determine_status(None, None, True)
    assert status == 'work-from-home'


# ==================== Check In/Check Out Tests ====================


def test_check_in_new_record(db_session):
    """Test check-in creates new attendance record."""
    emp = Employee(full_name='Alice', email='alice@test.com')
    db_session.add(emp)
    db_session.commit()
    db_session.refresh(emp)
    
    # Create shift for employee
    shift = Shift(
        name='Morning',
        start_time=time(9, 0),
        end_time=time(18, 0),
        grace_period_minutes=5,
    )
    db_session.add(shift)
    db_session.commit()
    db_session.refresh(shift)
    
    # Assign shift to employee
    assignment = EmployeeShiftAssignment(
        employee_id=emp.id,
        shift_id=shift.id,
        start_date=date(2024, 5, 1),
        is_active=True,
    )
    db_session.add(assignment)
    db_session.commit()
    
    # Check in
    check_in_time = datetime(2024, 5, 1, 9, 10, tzinfo=timezone.utc)
    request = CheckInRequest(
        employee_id=emp.id,
        attendance_date=date(2024, 5, 1),
        check_in_time=check_in_time,
    )
    
    result = check_in(request, db_session)
    
    assert result.employee_id == emp.id
    assert result.status == 'present'
    assert result.is_late is True  # 10 minutes - 5 grace = 5 minutes late (above 0)
    assert result.late_minutes > 0


def test_check_in_updates_existing_record(db_session):
    """Test check-in updates existing attendance record."""
    emp = Employee(full_name='Bob', email='bob@test.com')
    db_session.add(emp)
    db_session.commit()
    db_session.refresh(emp)
    
    # Create existing attendance
    existing = Attendance(
        employee_id=emp.id,
        attendance_date=date(2024, 5, 1),
        status='absent',
    )
    db_session.add(existing)
    db_session.commit()
    
    # Check in
    check_in_time = datetime(2024, 5, 1, 9, 0, tzinfo=timezone.utc)
    request = CheckInRequest(
        employee_id=emp.id,
        attendance_date=date(2024, 5, 1),
        check_in_time=check_in_time,
    )
    
    result = check_in(request, db_session)
    
    assert result.id == existing.id  # Same record
    assert result.status == 'present'
    assert result.check_in_time == check_in_time


def test_check_in_succeeds_when_audit_log_write_fails(db_session, monkeypatch):
    """Test check-in still succeeds if audit logging fails after commit."""
    emp = Employee(full_name='Eve', email='eve@test.com')
    db_session.add(emp)
    db_session.commit()
    db_session.refresh(emp)

    shift = Shift(
        name='Morning',
        start_time=time(9, 0),
        end_time=time(18, 0),
        grace_period_minutes=5,
    )
    db_session.add(shift)
    db_session.commit()
    db_session.refresh(shift)

    assignment = EmployeeShiftAssignment(
        employee_id=emp.id,
        shift_id=shift.id,
        start_date=date(2024, 5, 1),
        is_active=True,
    )
    db_session.add(assignment)
    db_session.commit()

    class FailingAuditLog:
        def __init__(self, *args, **kwargs):
            raise RuntimeError('audit log unavailable')

    monkeypatch.setattr('app.db.models.AuditLog', FailingAuditLog)

    request = CheckInRequest(
        employee_id=emp.id,
        attendance_date=date(2024, 5, 1),
        check_in_time=datetime(2024, 5, 1, 9, 10, tzinfo=timezone.utc),
    )

    result = check_in(request, db_session)

    assert result.employee_id == emp.id
    assert result.status == 'present'
    assert db_session.query(Attendance).filter(Attendance.employee_id == emp.id).count() == 1


def test_check_out_with_check_in(db_session):
    """Test check-out updates attendance with working hours."""
    emp = Employee(full_name='Carol', email='carol@test.com')
    db_session.add(emp)
    db_session.commit()
    db_session.refresh(emp)
    
    # Create attendance with check-in
    check_in_time = datetime(2024, 5, 1, 9, 0, tzinfo=timezone.utc)
    attendance = Attendance(
        employee_id=emp.id,
        attendance_date=date(2024, 5, 1),
        check_in_time=check_in_time,
        status='present',
    )
    db_session.add(attendance)
    db_session.commit()
    db_session.refresh(attendance)
    
    # Check out
    check_out_time = datetime(2024, 5, 1, 13, 0, tzinfo=timezone.utc)  # 4 hours
    request = CheckOutRequest(
        employee_id=emp.id,
        attendance_date=date(2024, 5, 1),
        check_out_time=check_out_time,
    )
    
    result = check_out(request, db_session)
    
    assert result.check_out_time == check_out_time
    assert result.is_half_day is False  # 4 hours = half-day threshold


def test_check_out_half_day(db_session):
    """Test check-out marks as half-day when below threshold."""
    emp = Employee(full_name='Dan', email='dan@test.com')
    db_session.add(emp)
    db_session.commit()
    db_session.refresh(emp)
    
    # Create attendance
    check_in_time = datetime(2024, 5, 1, 14, 0, tzinfo=timezone.utc)
    attendance = Attendance(
        employee_id=emp.id,
        attendance_date=date(2024, 5, 1),
        check_in_time=check_in_time,
        status='present',
    )
    db_session.add(attendance)
    db_session.commit()
    db_session.refresh(attendance)
    
    # Check out after 3 hours (below 4-hour half-day threshold)
    check_out_time = datetime(2024, 5, 1, 17, 0, tzinfo=timezone.utc)
    request = CheckOutRequest(
        employee_id=emp.id,
        attendance_date=date(2024, 5, 1),
        check_out_time=check_out_time,
    )
    
    result = check_out(request, db_session)
    
    assert result.is_half_day is True


# ==================== Attendance Summary Tests ====================


def test_attendance_summary_mixed_records(db_session):
    """Test attendance summary with various attendance types."""
    emp = Employee(full_name='Eve', email='eve@test.com')
    db_session.add(emp)
    db_session.commit()
    db_session.refresh(emp)
    
    # Create various attendance records for the month
    records = [
        Attendance(employee_id=emp.id, attendance_date=date(2024, 5, 1), status='present', is_late=False),
        Attendance(employee_id=emp.id, attendance_date=date(2024, 5, 2), status='present', is_late=True),
        Attendance(employee_id=emp.id, attendance_date=date(2024, 5, 3), status='absent', is_late=False),
        Attendance(employee_id=emp.id, attendance_date=date(2024, 5, 4), status='present', is_half_day=True),
        Attendance(employee_id=emp.id, attendance_date=date(2024, 5, 5), status='work-from-home', is_work_from_home=True),
    ]
    
    for record in records:
        db_session.add(record)
    db_session.commit()
    
    # Get summary
    summary = get_employee_attendance_summary(
        emp.id,
        date(2024, 5, 1),
        date(2024, 5, 5),
        db_session,
    )
    
    assert summary.total_days == 5
    assert summary.present_days == 3
    assert summary.absent_days == 1
    assert summary.half_days == 1
    assert summary.work_from_home_days == 1
    assert summary.late_days == 1
    assert len(summary.records) == 5


def test_attendance_summary_empty(db_session):
    """Test attendance summary for period with no records."""
    emp = Employee(full_name='Frank', email='frank@test.com')
    db_session.add(emp)
    db_session.commit()
    db_session.refresh(emp)
    
    # Get summary for month with no attendance
    summary = get_employee_attendance_summary(
        emp.id,
        date(2024, 5, 1),
        date(2024, 5, 31),
        db_session,
    )
    
    assert summary.total_days == 31
    assert summary.present_days == 0
    assert summary.absent_days == 0
    assert len(summary.records) == 0


def test_attendance_summary_date_range(db_session):
    """Test attendance summary respects date range."""
    emp = Employee(full_name='Grace', email='grace@test.com')
    db_session.add(emp)
    db_session.commit()
    db_session.refresh(emp)
    
    # Create records across multiple months
    for day in range(1, 31):
        record = Attendance(
            employee_id=emp.id,
            attendance_date=date(2024, 5, day),
            status='present',
        )
        db_session.add(record)
    db_session.commit()
    
    # Get summary for specific week
    summary = get_employee_attendance_summary(
        emp.id,
        date(2024, 5, 1),
        date(2024, 5, 7),
        db_session,
    )
    
    assert summary.total_days == 7
    assert summary.present_days == 7
    assert len(summary.records) == 7
