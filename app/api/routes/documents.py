from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
import shutil
import os
import uuid
from pathlib import Path
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

UPLOAD_DIR = Path(__file__).resolve().parents[3] / 'uploads' / 'employee_documents'
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

@router.post('/')
async def upload_document(
    employee_id: str = Form(...),
    document_type: str = Form(...),
    file: UploadFile = File(...),
    user: User = Depends(require_permissions('manage_employee')),
    db: Session = Depends(get_db)
):
    emp = db.query(Employee).filter(Employee.id == employee_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")

    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename missing")

    ext = file.filename.split('.')[-1] if '.' in file.filename else ''
    new_filename = f"{uuid.uuid4().hex}.{ext}"
    file_path = UPLOAD_DIR / new_filename

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # In DB, save the relative path from the server root or just the identifier
    db_path = f"employee_documents/{new_filename}"

    doc = EmployeeDocument(
        employee_id=employee_id,
        document_type=document_type,
        file_name=db_path
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc
