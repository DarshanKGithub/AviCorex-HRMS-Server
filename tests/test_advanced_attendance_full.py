"""Tests for the advanced attendance (timesheets, overtime, comp-off) workflow."""

from datetime import date, datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.database import Base
from app.db.models import Employee, Timesheet, OvertimeRequest, CompOffRequest
from app.schemas.advanced_attendance import (
    TimesheetCreate,
    OvertimeRequestCreate,
    CompOffRequestCreate,
)
from app.services.advanced_attendance_service import (
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


@pytest.fixture()
def db_session():
    engine = create_engine('sqlite:///:memory:', future=True)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
    session = Session()
    try:
        yield session
    finally:
        session.close()


# --- Timesheet Tests ---

def test_create_timesheet_draft(db_session):
    employee = Employee(full_name='Alice', email='alice@example.com')
    db_session.add(employee)
    db_session.commit()
    db_session.refresh(employee)

    payload = TimesheetCreate(
        employee_id=employee.id,
        date=date(2026, 5, 7),
        task_description='Completed API implementation',
        hours_worked=8.5,
    )

    ts = create_timesheet(payload, db_session)

    assert ts.employee_id == employee.id
    assert ts.status == 'Draft'
    assert ts.hours_worked == 8.5


def test_get_timesheets_filtered_by_employee(db_session):
    employee1 = Employee(full_name='Alice', email='alice@example.com')
    employee2 = Employee(full_name='Bob', email='bob@example.com')
    db_session.add_all([employee1, employee2])
    db_session.commit()
    db_session.refresh(employee1)
    db_session.refresh(employee2)

    ts1 = Timesheet(
        employee_id=employee1.id,
        date=date(2026, 5, 7),
        task_description='Task 1',
        hours_worked=8.0,
    )
    ts2 = Timesheet(
        employee_id=employee2.id,
        date=date(2026, 5, 7),
        task_description='Task 2',
        hours_worked=7.5,
    )
    db_session.add_all([ts1, ts2])
    db_session.commit()

    items, total = get_timesheets(db_session, employee_id=employee1.id)

    assert total == 1
    assert len(items) == 1
    assert items[0].employee_id == employee1.id


def test_update_timesheet_draft_only(db_session):
    employee = Employee(full_name='Cara', email='cara@example.com')
    db_session.add(employee)
    db_session.commit()
    db_session.refresh(employee)

    ts = Timesheet(
        employee_id=employee.id,
        date=date(2026, 5, 7),
        task_description='Initial task',
        hours_worked=8.0,
    )
    db_session.add(ts)
    db_session.commit()
    db_session.refresh(ts)

    payload = TimesheetCreate(
        employee_id=employee.id,
        date=date(2026, 5, 7),
        task_description='Updated task',
        hours_worked=7.5,
    )

    updated = update_timesheet(ts.id, payload, employee.id, db_session)

    assert updated.task_description == 'Updated task'
    assert updated.hours_worked == 7.5


# --- Overtime Request Tests ---

def test_create_overtime_request_pending(db_session):
    employee = Employee(full_name='Dan', email='dan@example.com')
    db_session.add(employee)
    db_session.commit()
    db_session.refresh(employee)

    payload = OvertimeRequestCreate(
        employee_id=employee.id,
        date=date(2026, 5, 7),
        hours=2.0,
        reason='Critical bug fix',
    )

    ot = create_overtime_request(payload, db_session)

    assert ot.employee_id == employee.id
    assert ot.status == 'Pending'
    assert ot.hours == 2.0


def test_approve_overtime_request(db_session):
    employee = Employee(full_name='Eve', email='eve@example.com')
    approver = Employee(full_name='Manager', email='manager@example.com')
    db_session.add_all([employee, approver])
    db_session.commit()
    db_session.refresh(employee)
    db_session.refresh(approver)

    ot = OvertimeRequest(
        employee_id=employee.id,
        date=date(2026, 5, 7),
        hours=3.0,
        reason='Project deadline',
    )
    db_session.add(ot)
    db_session.commit()
    db_session.refresh(ot)

    approved = approve_overtime(ot.id, approver.id, db_session)

    assert approved.status == 'Approved'
    assert approved.approver_id == approver.id


def test_reject_overtime_request(db_session):
    employee = Employee(full_name='Finn', email='finn@example.com')
    approver = Employee(full_name='HR', email='hr@example.com')
    db_session.add_all([employee, approver])
    db_session.commit()
    db_session.refresh(employee)
    db_session.refresh(approver)

    ot = OvertimeRequest(
        employee_id=employee.id,
        date=date(2026, 5, 7),
        hours=2.0,
    )
    db_session.add(ot)
    db_session.commit()
    db_session.refresh(ot)

    rejected = reject_overtime(ot.id, approver.id, db_session)

    assert rejected.status == 'Rejected'
    assert rejected.approver_id == approver.id


def test_get_overtime_requests_by_status(db_session):
    employee = Employee(full_name='Grace', email='grace@example.com')
    db_session.add(employee)
    db_session.commit()
    db_session.refresh(employee)

    pending = OvertimeRequest(
        employee_id=employee.id,
        date=date(2026, 5, 7),
        hours=2.0,
        status='Pending',
    )
    approved = OvertimeRequest(
        employee_id=employee.id,
        date=date(2026, 5, 6),
        hours=1.5,
        status='Approved',
    )
    db_session.add_all([pending, approved])
    db_session.commit()

    items, total = get_overtime_requests(db_session, status_filter='Approved')

    assert total == 1
    assert items[0].status == 'Approved'


# --- Comp-Off Request Tests ---

def test_create_comp_off_request(db_session):
    employee = Employee(full_name='Henry', email='henry@example.com')
    db_session.add(employee)
    db_session.commit()
    db_session.refresh(employee)

    payload = CompOffRequestCreate(
        employee_id=employee.id,
        worked_date=date(2026, 5, 4),  # Saturday
        reason='Worked on client project',
    )

    co = create_comp_off_request(payload, db_session)

    assert co.employee_id == employee.id
    assert co.status == 'Pending'
    assert co.worked_date == date(2026, 5, 4)


def test_approve_comp_off_request(db_session):
    employee = Employee(full_name='Iris', email='iris@example.com')
    approver = Employee(full_name='Lead', email='lead@example.com')
    db_session.add_all([employee, approver])
    db_session.commit()
    db_session.refresh(employee)
    db_session.refresh(approver)

    co = CompOffRequest(
        employee_id=employee.id,
        worked_date=date(2026, 5, 4),
    )
    db_session.add(co)
    db_session.commit()
    db_session.refresh(co)

    approved = approve_comp_off(co.id, approver.id, db_session)

    assert approved.status == 'Approved'
    assert approved.approver_id == approver.id


def test_reject_comp_off_request(db_session):
    employee = Employee(full_name='Jack', email='jack@example.com')
    approver = Employee(full_name='Admin', email='admin@example.com')
    db_session.add_all([employee, approver])
    db_session.commit()
    db_session.refresh(employee)
    db_session.refresh(approver)

    co = CompOffRequest(
        employee_id=employee.id,
        worked_date=date(2026, 5, 4),
    )
    db_session.add(co)
    db_session.commit()
    db_session.refresh(co)

    rejected = reject_comp_off(co.id, approver.id, db_session)

    assert rejected.status == 'Rejected'
    assert rejected.approver_id == approver.id


def test_get_comp_off_requests_filtered(db_session):
    employee = Employee(full_name='Karen', email='karen@example.com')
    db_session.add(employee)
    db_session.commit()
    db_session.refresh(employee)

    co1 = CompOffRequest(
        employee_id=employee.id,
        worked_date=date(2026, 5, 4),
        status='Pending',
    )
    co2 = CompOffRequest(
        employee_id=employee.id,
        worked_date=date(2026, 5, 3),
        status='Approved',
    )
    db_session.add_all([co1, co2])
    db_session.commit()

    items, total = get_comp_off_requests(
        db_session,
        employee_id=employee.id,
        status_filter='Pending',
    )

    assert total == 1
    assert len(items) == 1
    assert items[0].status == 'Pending'
