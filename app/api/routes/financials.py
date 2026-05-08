from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.core.rbac import get_current_user, require_permissions
from app.db.database import get_db
from app.db.models import User, SalaryStructure, Reimbursement, EmployeeLoan
from app.schemas.financials import (
    SalaryStructureCreate, SalaryStructurePublic,
    ReimbursementCreate, ReimbursementPublic,
    EmployeeLoanCreate, EmployeeLoanPublic
)

router = APIRouter()

# --- Salary Structure ---

@router.post('/salary-structures', response_model=SalaryStructurePublic)
def create_salary_structure(
    payload: SalaryStructureCreate,
    user: User = Depends(require_permissions('process_payroll')),
    db: Session = Depends(get_db)
):
    existing = db.query(SalaryStructure).filter(SalaryStructure.employee_id == payload.employee_id).first()
    if existing:
        for k, v in payload.model_dump().items():
            setattr(existing, k, v)
        struct = existing
    else:
        struct = SalaryStructure(**payload.model_dump())
        db.add(struct)
    db.commit()
    db.refresh(struct)
    return SalaryStructurePublic.model_validate(struct, from_attributes=True)

@router.get('/salary-structures/{employee_id}', response_model=SalaryStructurePublic)
def get_salary_structure(
    employee_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if employee_id != user.id and user.role not in ['HR', 'Admin', 'Manager', 'CEO']:
        raise HTTPException(status_code=403, detail='Not authorized')

    struct = db.query(SalaryStructure).filter(SalaryStructure.employee_id == employee_id).first()
    if not struct:
        raise HTTPException(status_code=404, detail="Salary structure not found")
    return SalaryStructurePublic.model_validate(struct, from_attributes=True)

# --- Reimbursements ---

@router.post('/reimbursements', response_model=ReimbursementPublic)
def apply_reimbursement(
    payload: ReimbursementCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    reim = Reimbursement(**payload.model_dump(), employee_id=user.id)
    db.add(reim)
    db.commit()
    db.refresh(reim)
    return ReimbursementPublic.model_validate(reim, from_attributes=True)

@router.get('/reimbursements', response_model=list[ReimbursementPublic])
def list_reimbursements(
    employee_id: Optional[str] = Query(None),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(Reimbursement)
    if employee_id:
        if employee_id != user.id and user.role not in ['HR', 'Admin', 'Manager']:
            raise HTTPException(status_code=403, detail="Not authorized")
        query = query.filter(Reimbursement.employee_id == employee_id)
    else:
        if user.role not in ['HR', 'Admin', 'Manager']:
            query = query.filter(Reimbursement.employee_id == user.id)
            
    items = query.order_by(Reimbursement.applied_on.desc()).all()
    return [ReimbursementPublic.model_validate(i, from_attributes=True) for i in items]

@router.patch('/reimbursements/{id}/status', response_model=ReimbursementPublic)
def update_reimbursement_status(
    id: str,
    status: str = Query(...),
    user: User = Depends(require_permissions('process_payroll')),
    db: Session = Depends(get_db)
):
    reim = db.query(Reimbursement).filter(Reimbursement.id == id).first()
    if not reim:
        raise HTTPException(status_code=404, detail="Reimbursement not found")
    reim.status = status
    db.commit()
    db.refresh(reim)
    return ReimbursementPublic.model_validate(reim, from_attributes=True)

# --- Loans ---

@router.post('/loans', response_model=EmployeeLoanPublic)
def apply_loan(
    payload: EmployeeLoanCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    loan = EmployeeLoan(**payload.model_dump(), employee_id=user.id)
    db.add(loan)
    db.commit()
    db.refresh(loan)
    return EmployeeLoanPublic.model_validate(loan, from_attributes=True)

@router.get('/loans', response_model=list[EmployeeLoanPublic])
def list_loans(
    employee_id: Optional[str] = Query(None),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(EmployeeLoan)
    if employee_id:
        if employee_id != user.id and user.role not in ['HR', 'Admin', 'Manager']:
            raise HTTPException(status_code=403, detail="Not authorized")
        query = query.filter(EmployeeLoan.employee_id == employee_id)
    else:
        if user.role not in ['HR', 'Admin', 'Manager']:
            query = query.filter(EmployeeLoan.employee_id == user.id)
            
    items = query.order_by(EmployeeLoan.created_at.desc()).all()
    return [EmployeeLoanPublic.model_validate(i, from_attributes=True) for i in items]
