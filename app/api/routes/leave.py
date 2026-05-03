"""API routes for Leave Management (Phase 5)."""
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.leave import (
    LeaveRequestCreate,
    LeaveRequestPublic,
    PaginatedLeaveRequests,
    ApprovePayload,
    LeaveBalancePublic,
)
from app.services.leave_service import (
    create_leave_request,
    list_leave_requests,
    get_leave_request,
    approve_leave,
    get_leave_balances,
)
from app.services.auth_service import get_user_from_token

security = HTTPBearer(auto_error=False)
router = APIRouter()


@router.post('/requests', response_model=LeaveRequestPublic)
def request_leave_endpoint(
    payload: LeaveRequestCreate,
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: Session = Depends(get_db),
) -> LeaveRequestPublic:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Not authenticated')

    user = get_user_from_token(credentials.credentials, db=db)
    # user.id is user.id; map to employee id: login returns employee_id in user payload when available
    employee_id = getattr(user, 'id', None)
    # If user has employee mapping in DB, use that; otherwise assume user.id equals employee.id (demo)
    # create_leave_request will validate employee existence
    lr = create_leave_request(employee_id, payload, db)
    return LeaveRequestPublic.model_validate({
        'id': lr.id,
        'employee_id': lr.employee_id,
        'leave_type_id': lr.leave_type_id,
        'start_date': lr.start_date,
        'end_date': lr.end_date,
        'days_requested': lr.days_requested,
        'reason': lr.reason,
        'status': lr.status,
        'approver_id': lr.approver_id,
        'approved_at': lr.approved_at,
        'created_at': lr.created_at,
        'updated_at': lr.updated_at,
    })


@router.get('/requests', response_model=PaginatedLeaveRequests)
def list_requests_endpoint(
    employee_id: str | None = Query(None),
    status: str | None = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: Session = Depends(get_db),
) -> PaginatedLeaveRequests:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Not authenticated')

    user = get_user_from_token(credentials.credentials, db=db)
    # Employees may only list their own unless Admin/HR
    if user.role == 'Employee' and employee_id and employee_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Cannot view other employees requests')

    items, total = list_leave_requests(db, employee_id=employee_id, status_filter=status, page=page, size=size)
    return PaginatedLeaveRequests(
        items=[LeaveRequestPublic.model_validate({
            'id': r.id,
            'employee_id': r.employee_id,
            'leave_type_id': r.leave_type_id,
            'start_date': r.start_date,
            'end_date': r.end_date,
            'days_requested': r.days_requested,
            'reason': r.reason,
            'status': r.status,
            'approver_id': r.approver_id,
            'approved_at': r.approved_at,
            'created_at': r.created_at,
            'updated_at': r.updated_at,
        }) for r in items],
        total=total,
        page=page,
        size=size,
    )


@router.get('/requests/{request_id}', response_model=LeaveRequestPublic)
def get_request_endpoint(
    request_id: str,
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: Session = Depends(get_db),
):
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Not authenticated')

    user = get_user_from_token(credentials.credentials, db=db)
    lr = get_leave_request(request_id, db)
    if user.role == 'Employee' and lr.employee_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Cannot view other employees requests')

    return LeaveRequestPublic.model_validate({
        'id': lr.id,
        'employee_id': lr.employee_id,
        'leave_type_id': lr.leave_type_id,
        'start_date': lr.start_date,
        'end_date': lr.end_date,
        'days_requested': lr.days_requested,
        'reason': lr.reason,
        'status': lr.status,
        'approver_id': lr.approver_id,
        'approved_at': lr.approved_at,
        'created_at': lr.created_at,
        'updated_at': lr.updated_at,
    })


@router.post('/requests/{request_id}/approve', response_model=LeaveRequestPublic)
def approve_request_endpoint(
    request_id: str,
    payload: ApprovePayload,
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: Session = Depends(get_db),
):
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Not authenticated')

    user = get_user_from_token(credentials.credentials, db=db)
    # Only Manager/HR/Admin can approve
    if user.role not in ['Admin', 'HR', 'Manager']:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Insufficient privileges')

    # For Manager role, ensure they are manager of the employee
    lr = get_leave_request(request_id, db)
    if user.role == 'Manager':
        # ensure manager relationship (employee.manager_id == user.id)
        from app.db.models import Employee
        emp = db.query(Employee).filter(Employee.id == lr.employee_id).first()
        if not emp or emp.manager_id != user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Not authorized to approve this request')

    updated = approve_leave(request_id, user.id, payload.approve, db)
    return LeaveRequestPublic.model_validate({
        'id': updated.id,
        'employee_id': updated.employee_id,
        'leave_type_id': updated.leave_type_id,
        'start_date': updated.start_date,
        'end_date': updated.end_date,
        'days_requested': updated.days_requested,
        'reason': updated.reason,
        'status': updated.status,
        'approver_id': updated.approver_id,
        'approved_at': updated.approved_at,
        'created_at': updated.created_at,
        'updated_at': updated.updated_at,
    })


@router.get('/balances', response_model=list[LeaveBalancePublic])
def balances_endpoint(
    employee_id: str | None = Query(None),
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: Session = Depends(get_db),
):
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Not authenticated')
    user = get_user_from_token(credentials.credentials, db=db)
    if user.role == 'Employee' and employee_id and employee_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Cannot view other employees balances')

    if not employee_id:
        employee_id = user.id

    balances = get_leave_balances(employee_id, db)
    out = []
    for b in balances:
        out.append(LeaveBalancePublic.model_validate({
            'id': b.id,
            'employee_id': b.employee_id,
            'leave_type_id': b.leave_type_id,
            'year': b.year,
            'balance_days': b.balance_days,
            'created_at': b.created_at,
            'updated_at': b.updated_at,
        }))
    return out
