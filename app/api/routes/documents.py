from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.rbac import get_current_user, require_permissions
from app.db.database import get_db
from app.db.models import User, EmployeeDocument, Employee
from app.schemas.document import EmployeeDocumentPublic
from pydantic import BaseModel
from datetime import datetime

router = APIRouter()

class DocumentWithEmployeePublic(EmployeeDocumentPublic):
    employee_name: str

@router.get('/', response_model=list[DocumentWithEmployeePublic])
def get_all_documents(
    user: User = Depends(require_permissions('view_employee')),
    db: Session = Depends(get_db)
):
    docs = db.query(EmployeeDocument, Employee).join(Employee, EmployeeDocument.employee_id == Employee.id).all()
    
    result = []
    for doc, emp in docs:
        d_dict = doc.__dict__.copy()
        d_dict['employee_name'] = emp.full_name
        result.append(DocumentWithEmployeePublic.model_validate(d_dict, from_attributes=True))
    
    return result
