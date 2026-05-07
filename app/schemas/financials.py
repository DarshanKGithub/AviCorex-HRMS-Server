from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class SalaryStructureBase(BaseModel):
    base_salary: float
    hra: float
    da: float
    special_allowance: float
    pf_percentage: float
    esi_percentage: float
    tax_bracket_percentage: float

class SalaryStructureCreate(SalaryStructureBase):
    employee_id: str

class SalaryStructurePublic(SalaryStructureBase):
    id: str
    employee_id: str
    created_at: datetime

class ReimbursementCreate(BaseModel):
    expense_type: str
    amount: float
    receipt_url: Optional[str] = None
    description: Optional[str] = None

class ReimbursementPublic(ReimbursementCreate):
    id: str
    employee_id: str
    status: str
    applied_on: datetime

class EmployeeLoanCreate(BaseModel):
    loan_type: str
    amount: float
    interest_rate: float
    emi_amount: float
    remaining_balance: float

class EmployeeLoanPublic(EmployeeLoanCreate):
    id: str
    employee_id: str
    status: str
    created_at: datetime
