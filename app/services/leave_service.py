"""Services for leave request lifecycle and balance calculations."""
from datetime import datetime
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.db.models import LeaveRequest, LeaveType, LeaveBalance, Employee, AuditLog


def _days_between(start_date, end_date) -> int:
    # inclusive
    return (end_date - start_date).days + 1


def create_leave_request(employee_id: str, payload, db: Session) -> LeaveRequest:
    # payload: LeaveRequestCreate-like
    # Validate employee
    emp = db.query(Employee).filter(Employee.id == employee_id).first()
    if not emp:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Employee not found')

    lt = db.query(LeaveType).filter(LeaveType.id == payload.leave_type_id, LeaveType.is_active.is_(True)).first()
    if not lt:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Leave type not found')

    if payload.start_date > payload.end_date:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='start_date must be before end_date')

    days = _days_between(payload.start_date, payload.end_date)

    lr = LeaveRequest(
        employee_id=employee_id,
        leave_type_id=payload.leave_type_id,
        start_date=payload.start_date,
        end_date=payload.end_date,
        days_requested=days,
        reason=payload.reason,
        status='pending',
    )
    db.add(lr)
    db.commit()
    db.refresh(lr)

    # audit
    try:
        db.add(AuditLog(actor_id=None, action='create', object_type='leave_request', object_id=lr.id, data=str({'employee_id': employee_id, 'days': days})))
        db.commit()
    except Exception:
        db.rollback()

    return lr


def get_leave_request(leave_id: str, db: Session) -> LeaveRequest:
    lr = db.query(LeaveRequest).filter(LeaveRequest.id == leave_id).first()
    if not lr:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Leave request not found')
    return lr


def list_leave_requests(db: Session, employee_id: str | None = None, status_filter: str | None = None, page: int = 1, size: int = 20):
    query = db.query(LeaveRequest)
    if employee_id:
        query = query.filter(LeaveRequest.employee_id == employee_id)
    if status_filter:
        query = query.filter(LeaveRequest.status == status_filter)

    total = query.with_entities(func.count(LeaveRequest.id)).scalar() or 0
    items = query.order_by(LeaveRequest.created_at.desc()).offset((page - 1) * size).limit(size).all()
    return items, int(total)


def _get_or_create_balance(employee_id: str, leave_type_id: str, year: int, db: Session) -> LeaveBalance:
    bal = db.query(LeaveBalance).filter(LeaveBalance.employee_id == employee_id, LeaveBalance.leave_type_id == leave_type_id, LeaveBalance.year == year).first()
    if bal:
        return bal
    # try to create from LeaveType default
    lt = db.query(LeaveType).filter(LeaveType.id == leave_type_id).first()
    default_days = lt.default_days_per_year if lt else 0
    bal = LeaveBalance(employee_id=employee_id, leave_type_id=leave_type_id, year=year, balance_days=default_days)
    db.add(bal)
    db.commit()
    db.refresh(bal)
    return bal


def approve_leave(leave_id: str, approver_id: str, approve: bool, db: Session) -> LeaveRequest:
    lr = get_leave_request(leave_id, db)
    if lr.status not in ['pending']:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Leave request is not pending')

    if approve:
        year = lr.start_date.year
        bal = _get_or_create_balance(lr.employee_id, lr.leave_type_id, year, db)
        if bal.balance_days < lr.days_requested:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Insufficient leave balance')
        bal.balance_days -= lr.days_requested
        bal.updated_at = datetime.now()
        lr.status = 'approved'
        lr.approver_id = approver_id
        lr.approved_at = datetime.now()
        lr.updated_at = datetime.now()
        db.add(bal)
        db.add(lr)
        db.commit()
        db.refresh(lr)
    else:
        lr.status = 'rejected'
        lr.approver_id = approver_id
        lr.approved_at = datetime.now()
        lr.updated_at = datetime.now()
        db.add(lr)
        db.commit()
        db.refresh(lr)

    try:
        db.add(AuditLog(actor_id=approver_id, action='approve' if approve else 'reject', object_type='leave_request', object_id=lr.id, data=str({'status': lr.status})))
        db.commit()
    except Exception:
        db.rollback()

    return lr


def get_leave_balances(employee_id: str, db: Session) -> list[LeaveBalance]:
    return db.query(LeaveBalance).filter(LeaveBalance.employee_id == employee_id).all()
