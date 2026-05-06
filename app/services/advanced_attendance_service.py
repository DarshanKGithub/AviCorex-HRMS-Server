from datetime import date
from typing import Tuple, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc
from fastapi import HTTPException, status

from app.db.models import (
    Timesheet,
    OvertimeRequest,
    AttendanceRegularization,
    CompOffRequest,
    BiometricDevice,
    BiometricLog,
    Roster,
    RosterEntry,
    Attendance
)
from app.schemas.advanced_attendance import (
    TimesheetCreate,
    OvertimeRequestCreate,
    AttendanceRegularizationCreate,
    CompOffRequestCreate,
    BiometricDeviceCreate,
    BiometricLogCreate,
    RosterCreate,
    RosterEntryCreate
)


# --- Attendance Regularization ---

def create_attendance_regularization(payload: AttendanceRegularizationCreate, db: Session) -> AttendanceRegularization:
    reg = AttendanceRegularization(**payload.model_dump())
    db.add(reg)
    db.commit()
    db.refresh(reg)
    return reg


def get_regularizations(
    db: Session,
    employee_id: Optional[str] = None,
    status_filter: Optional[str] = None,
    page: int = 1,
    size: int = 20
) -> Tuple[List[AttendanceRegularization], int]:
    query = db.query(AttendanceRegularization)
    if employee_id:
        query = query.filter(AttendanceRegularization.employee_id == employee_id)
    if status_filter:
        query = query.filter(AttendanceRegularization.status == status_filter)
    
    total = query.count()
    items = query.order_by(desc(AttendanceRegularization.created_at)).offset((page - 1) * size).limit(size).all()
    return items, total


def approve_regularization(reg_id: str, approver_id: str, db: Session) -> AttendanceRegularization:
    reg = db.query(AttendanceRegularization).filter(AttendanceRegularization.id == reg_id).first()
    if not reg:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Regularization not found")
    
    if reg.status != 'Pending':
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only pending requests can be approved")
    
    reg.status = 'Approved'
    reg.approver_id = approver_id
    
    # Update the actual attendance record
    if reg.attendance_id:
        attendance = db.query(Attendance).filter(Attendance.id == reg.attendance_id).first()
    else:
        # Create a new attendance record for that date
        attendance = db.query(Attendance).filter(
            Attendance.employee_id == reg.employee_id,
            Attendance.attendance_date == reg.date
        ).first()
        if not attendance:
            attendance = Attendance(
                employee_id=reg.employee_id,
                attendance_date=reg.date,
                status='present'
            )
            db.add(attendance)
            db.flush()
            reg.attendance_id = attendance.id

    if reg.requested_check_in:
        attendance.check_in_time = reg.requested_check_in
    if reg.requested_check_out:
        attendance.check_out_time = reg.requested_check_out
        
    db.commit()
    db.refresh(reg)
    return reg


def reject_regularization(reg_id: str, approver_id: str, db: Session) -> AttendanceRegularization:
    reg = db.query(AttendanceRegularization).filter(AttendanceRegularization.id == reg_id).first()
    if not reg:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Regularization not found")
    
    if reg.status != 'Pending':
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only pending requests can be rejected")
    
    reg.status = 'Rejected'
    reg.approver_id = approver_id
    db.commit()
    db.refresh(reg)
    return reg


# --- Scaffolds for other Step 3 functionalities ---

def create_timesheet(payload: TimesheetCreate, db: Session) -> Timesheet:
    ts = Timesheet(**payload.model_dump())
    db.add(ts)
    db.commit()
    db.refresh(ts)
    return ts

def create_overtime_request(payload: OvertimeRequestCreate, db: Session) -> OvertimeRequest:
    ot = OvertimeRequest(**payload.model_dump())
    db.add(ot)
    db.commit()
    db.refresh(ot)
    return ot

def create_comp_off_request(payload: CompOffRequestCreate, db: Session) -> CompOffRequest:
    co = CompOffRequest(**payload.model_dump())
    db.add(co)
    db.commit()
    db.refresh(co)
    return co

def create_biometric_device(payload: BiometricDeviceCreate, db: Session) -> BiometricDevice:
    device = BiometricDevice(**payload.model_dump())
    db.add(device)
    db.commit()
    db.refresh(device)
    return device

def log_biometric(payload: BiometricLogCreate, db: Session) -> BiometricLog:
    log = BiometricLog(**payload.model_dump())
    db.add(log)
    db.commit()
    db.refresh(log)
    return log

def create_roster(payload: RosterCreate, db: Session) -> Roster:
    r = Roster(**payload.model_dump())
    db.add(r)
    db.commit()
    db.refresh(r)
    return r

def assign_roster_entry(payload: RosterEntryCreate, db: Session) -> RosterEntry:
    entry = RosterEntry(**payload.model_dump())
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry
