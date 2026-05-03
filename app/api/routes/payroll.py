"""API routes for Payroll Management (Phase 6)."""
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.payroll import (
    SalaryPublic,
    PayslipPublic,
    PayslipDetailPublic,
    PayslipCreate,
    PaginatedPayslips,
    BatchPayrollRequest,
    BatchPayrollResult,
    SalaryHistoryResponse,
    UpdateSalaryRequest,
)
from app.services.payroll_service import (
    create_payslip,
    get_payslip,
    list_payslips,
    approve_payslip,
    mark_payslip_paid,
    get_or_create_salary,
    get_payslip_details,
    send_payslip_email,
    run_batch_payroll,
    get_salary_history,
    update_salary,
)
from app.services.auth_service import get_user_from_token

security = HTTPBearer(auto_error=False)
router = APIRouter()


@router.get('/salary', response_model=SalaryPublic)
def get_salary_endpoint(
    employee_id: str | None = Query(None),
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: Session = Depends(get_db),
) -> SalaryPublic:
    """Get salary details for an employee."""
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Not authenticated')

    user = get_user_from_token(credentials.credentials, db=db)
    
    # Default to requesting user's own salary
    if not employee_id:
        employee_id = user.id
    
    # Employees can only view their own salary unless Admin/HR
    if user.role == 'Employee' and employee_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Cannot view other employees salary')
    
    sal = get_or_create_salary(employee_id, db)
    return SalaryPublic.model_validate({
        'id': sal.id,
        'employee_id': sal.employee_id,
        'base_salary': sal.base_salary,
        'grade': sal.grade,
        'currency': sal.currency,
        'effective_from': sal.effective_from,
        'effective_to': sal.effective_to,
        'is_active': sal.is_active,
        'created_at': sal.created_at,
        'updated_at': sal.updated_at,
    })


@router.post('/payslips', response_model=PayslipPublic)
def create_payslip_endpoint(
    payload: PayslipCreate,
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: Session = Depends(get_db),
) -> PayslipPublic:
    """Generate a payslip for an employee (auto-calculates days_worked from attendance)."""
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Not authenticated')

    user = get_user_from_token(credentials.credentials, db=db)
    
    # Only HR/Admin can create payslips
    if user.role not in ['Admin', 'HR']:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Only HR/Admin can create payslips')
    
    # Auto-calculate days_worked and days_absent from attendance records
    ps = create_payslip(
        employee_id=payload.employee_id,
        month=payload.month,
        year=payload.year,
        db=db
    )
    
    return PayslipPublic.model_validate({
        'id': ps.id,
        'employee_id': ps.employee_id,
        'month': ps.month,
        'year': ps.year,
        'base_salary': ps.base_salary,
        'gross_salary': ps.gross_salary,
        'total_deductions': ps.total_deductions,
        'total_tax': ps.total_tax,
        'net_salary': ps.net_salary,
        'days_worked': ps.days_worked,
        'days_absent': ps.days_absent,
        'status': ps.status,
        'processed_by': ps.processed_by,
        'processed_at': ps.processed_at,
        'created_at': ps.created_at,
        'updated_at': ps.updated_at,
    })


@router.get('/payslips', response_model=PaginatedPayslips)
def list_payslips_endpoint(
    employee_id: str | None = Query(None),
    month: int | None = Query(None, ge=1, le=12),
    year: int | None = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: Session = Depends(get_db),
) -> PaginatedPayslips:
    """List payslips with optional filters."""
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Not authenticated')

    user = get_user_from_token(credentials.credentials, db=db)
    
    # Employees can only view their own payslips
    if user.role == 'Employee' and employee_id and employee_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Cannot view other employees payslips')
    
    if user.role == 'Employee' and not employee_id:
        employee_id = user.id
    
    items, total = list_payslips(db, employee_id=employee_id, month=month, year=year, page=page, size=size)
    
    return PaginatedPayslips(
        items=[PayslipPublic.model_validate({
            'id': p.id,
            'employee_id': p.employee_id,
            'month': p.month,
            'year': p.year,
            'base_salary': p.base_salary,
            'gross_salary': p.gross_salary,
            'total_deductions': p.total_deductions,
            'total_tax': p.total_tax,
            'net_salary': p.net_salary,
            'days_worked': p.days_worked,
            'days_absent': p.days_absent,
            'status': p.status,
            'processed_by': p.processed_by,
            'processed_at': p.processed_at,
            'created_at': p.created_at,
            'updated_at': p.updated_at,
        }) for p in items],
        total=total,
        page=page,
        size=size,
    )


@router.get('/payslips/{payslip_id}', response_model=PayslipDetailPublic)
def get_payslip_endpoint(
    payslip_id: str,
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: Session = Depends(get_db),
):
    """Get detailed payslip with components breakdown."""
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Not authenticated')

    user = get_user_from_token(credentials.credentials, db=db)
    ps = get_payslip(payslip_id, db)
    
    # Employees can only view their own payslips
    if user.role == 'Employee' and ps.employee_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Cannot view other employees payslips')
    
    # Get components
    from app.db.models import PayslipComponent
    components = db.query(PayslipComponent).filter(PayslipComponent.payslip_id == payslip_id).all()
    
    return PayslipDetailPublic.model_validate({
        'id': ps.id,
        'employee_id': ps.employee_id,
        'month': ps.month,
        'year': ps.year,
        'base_salary': ps.base_salary,
        'gross_salary': ps.gross_salary,
        'total_deductions': ps.total_deductions,
        'total_tax': ps.total_tax,
        'net_salary': ps.net_salary,
        'days_worked': ps.days_worked,
        'days_absent': ps.days_absent,
        'status': ps.status,
        'processed_by': ps.processed_by,
        'processed_at': ps.processed_at,
        'created_at': ps.created_at,
        'updated_at': ps.updated_at,
        'components': [
            {
                'id': c.id,
                'component_name': c.component_name,
                'component_type': c.component_type,
                'amount': c.amount,
            } for c in components
        ],
    })


@router.post('/payslips/{payslip_id}/approve', response_model=PayslipPublic)
def approve_payslip_endpoint(
    payslip_id: str,
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: Session = Depends(get_db),
):
    """Approve a payslip (HR/Admin only)."""
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Not authenticated')

    user = get_user_from_token(credentials.credentials, db=db)
    
    # Only HR/Admin/Manager can approve
    if user.role not in ['Admin', 'HR', 'Manager']:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Insufficient privileges')
    
    ps = approve_payslip(payslip_id, user.id, db)
    
    return PayslipPublic.model_validate({
        'id': ps.id,
        'employee_id': ps.employee_id,
        'month': ps.month,
        'year': ps.year,
        'base_salary': ps.base_salary,
        'gross_salary': ps.gross_salary,
        'total_deductions': ps.total_deductions,
        'total_tax': ps.total_tax,
        'net_salary': ps.net_salary,
        'days_worked': ps.days_worked,
        'days_absent': ps.days_absent,
        'status': ps.status,
        'processed_by': ps.processed_by,
        'processed_at': ps.processed_at,
        'created_at': ps.created_at,
        'updated_at': ps.updated_at,
    })


@router.post('/payslips/{payslip_id}/mark-paid', response_model=PayslipPublic)
def mark_paid_endpoint(
    payslip_id: str,
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: Session = Depends(get_db),
):
    """Mark payslip as paid (HR/Admin only)."""
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Not authenticated')

    user = get_user_from_token(credentials.credentials, db=db)
    
    if user.role not in ['Admin', 'HR']:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Only HR/Admin can mark payslips as paid')
    
    ps = mark_payslip_paid(payslip_id, user.id, db)
    
    return PayslipPublic.model_validate({
        'id': ps.id,
        'employee_id': ps.employee_id,
        'month': ps.month,
        'year': ps.year,
        'base_salary': ps.base_salary,
        'gross_salary': ps.gross_salary,
        'total_deductions': ps.total_deductions,
        'total_tax': ps.total_tax,
        'net_salary': ps.net_salary,
        'days_worked': ps.days_worked,
        'days_absent': ps.days_absent,
        'status': ps.status,
        'processed_by': ps.processed_by,
        'processed_at': ps.processed_at,
        'created_at': ps.created_at,
        'updated_at': ps.updated_at,
    })


@router.get('/payslips/{payslip_id}/pdf')
def download_payslip_pdf(
    payslip_id: str,
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: Session = Depends(get_db),
):
    """Download payslip as PDF."""
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Not authenticated')

    user = get_user_from_token(credentials.credentials, db=db)
    ps = get_payslip(payslip_id, db)
    
    # Permission check: Employee can only download their own, others need Admin/HR role
    if user.role == 'Employee' and ps.employee_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Not authorized to download this payslip')
    
    # Get payslip details
    payslip_data = get_payslip_details(payslip_id, db)
    
    # Generate PDF
    from app.core.payroll_utils import generate_payslip_pdf_bytes
    pdf_bytes = generate_payslip_pdf_bytes(payslip_data)
    
    if not pdf_bytes or isinstance(pdf_bytes, str):
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail='PDF generation failed')
    
    month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    month_name = month_names[payslip_data['month'] - 1]
    filename = f"Payslip_{month_name}_{payslip_data['year']}.pdf"
    
    return FileResponse(
        iter([pdf_bytes]),
        media_type='application/pdf',
        filename=filename
    )


@router.post('/payslips/{payslip_id}/send-email')
def send_payslip_email_endpoint(
    payslip_id: str,
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: Session = Depends(get_db),
) -> dict:
    """Send payslip via email to employee."""
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Not authenticated')

    user = get_user_from_token(credentials.credentials, db=db)
    
    # Only HR/Admin can send payslips
    if user.role not in ['Admin', 'HR']:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Only HR/Admin can send payslips via email')
    
    try:
        success = send_payslip_email(payslip_id, db)
        if success:
            return {'success': True, 'message': 'Payslip sent successfully'}
        else:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail='Failed to send payslip email')
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f'Error sending email: {str(e)}')


@router.post('/runs', response_model=BatchPayrollResult)
def run_batch_payroll_endpoint(
    payload: BatchPayrollRequest,
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: Session = Depends(get_db),
) -> BatchPayrollResult:
    """Run batch payroll for all active employees for a given month/year."""
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Not authenticated')

    user = get_user_from_token(credentials.credentials, db=db)
    
    # Only Admin/HR can run batch payroll
    if user.role not in ['Admin', 'HR']:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Only Admin/HR can run batch payroll')
    
    # Validate month and year
    if payload.month < 1 or payload.month > 12:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Invalid month (must be 1-12)')
    
    if payload.year < 2000:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Invalid year')
    
    result = run_batch_payroll(payload.month, payload.year, db)
    
    return BatchPayrollResult(**result)


@router.get('/salary-history', response_model=SalaryHistoryResponse)
def get_salary_history_endpoint(
    employee_id: str | None = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: Session = Depends(get_db),
) -> SalaryHistoryResponse:
    """Get salary history for an employee."""
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Not authenticated')

    user = get_user_from_token(credentials.credentials, db=db)
    
    # Default to requesting user's own history
    if not employee_id:
        employee_id = user.id
    
    # Permission check: Employee can only view their own, others need Admin/HR role
    if user.role == 'Employee' and employee_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Not authorized to view this salary history')
    
    result = get_salary_history(employee_id, db, page=page, size=size)
    
    return SalaryHistoryResponse(**result)


@router.put('/salary', response_model=SalaryPublic)
def update_salary_endpoint(
    payload: UpdateSalaryRequest,
    employee_id: str = Query(...),
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: Session = Depends(get_db),
) -> SalaryPublic:
    """Update employee salary (create new salary entry and mark old as inactive)."""
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Not authenticated')

    user = get_user_from_token(credentials.credentials, db=db)
    
    # Only Admin/HR can update salaries
    if user.role not in ['Admin', 'HR']:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Only Admin/HR can update salaries')
    
    # Update salary and create history entry
    new_salary = update_salary(
        employee_id=employee_id,
        new_base_salary=payload.base_salary,
        grade=payload.grade,
        effective_from=payload.effective_from,
        reason=payload.reason,
        modified_by_id=user.id,
        db=db
    )
    
    return SalaryPublic.model_validate({
        'id': new_salary.id,
        'employee_id': new_salary.employee_id,
        'base_salary': new_salary.base_salary,
        'grade': new_salary.grade,
        'currency': new_salary.currency,
        'effective_from': new_salary.effective_from,
        'effective_to': new_salary.effective_to,
        'is_active': new_salary.is_active,
        'created_at': new_salary.created_at,
        'updated_at': new_salary.updated_at,
    })
