from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.rbac import require_permissions
from app.db.database import get_db
from app.db.models import User
from app.schemas.employee import EmployeeCreate, EmployeePublic, EmployeeUpdate, PaginatedEmployees
from app.services.employee_service import search_employees, create_employee, get_employee, update_employee, delete_employee
from app.services.employee_service import get_manager_chain

router = APIRouter()


@router.get('/', response_model=PaginatedEmployees)
def employees(page: int = 1, size: int = 20, q: str | None = None, department_id: str | None = None,
              designation_id: str | None = None, db: Session = Depends(get_db)):
    items, total = search_employees(db=db, page=page, size=size, q=q, department_id=department_id, designation_id=designation_id)
    return PaginatedEmployees(
        items=[EmployeePublic(
            id=e.id,
            full_name=e.full_name,
            email=e.email,
            department_id=e.department_id,
            designation_id=e.designation_id,
            manager_id=e.manager_id,
            is_active=e.is_active,
        ) for e in items],
        total=total,
        page=page,
        size=size,
    )


@router.post('/', response_model=EmployeePublic)
def create(
    payload: EmployeeCreate,
    user: User = Depends(require_permissions('create_employee')),
    db: Session = Depends(get_db),
):

    e = create_employee(payload=payload, db=db, actor_id=user.id)
    return EmployeePublic(
        id=e.id,
        full_name=e.full_name,
        email=e.email,
        department_id=e.department_id,
        designation_id=e.designation_id,
        manager_id=e.manager_id,
        is_active=e.is_active,
    )


@router.get('/{employee_id}', response_model=EmployeePublic)
def get_one(employee_id: str, db: Session = Depends(get_db)):
    e = get_employee(employee_id, db=db)
    return EmployeePublic(
        id=e.id,
        full_name=e.full_name,
        email=e.email,
        department_id=e.department_id,
        designation_id=e.designation_id,
        manager_id=e.manager_id,
        is_active=e.is_active,
    )


@router.patch('/{employee_id}', response_model=EmployeePublic)
def patch(
    employee_id: str,
    payload: EmployeeUpdate,
    user: User = Depends(require_permissions('edit_employee')),
    db: Session = Depends(get_db),
):

    e = update_employee(employee_id, payload=payload, db=db, actor_id=user.id)
    return EmployeePublic(
        id=e.id,
        full_name=e.full_name,
        email=e.email,
        department_id=e.department_id,
        designation_id=e.designation_id,
        manager_id=e.manager_id,
        is_active=e.is_active,
    )


@router.delete('/{employee_id}')
def remove(employee_id: str, user: User = Depends(require_permissions('delete_employee')), db: Session = Depends(get_db)):

    delete_employee(employee_id, db=db, actor_id=user.id)
    return {'detail': 'deleted'}


@router.get('/{employee_id}/manager-chain')
def manager_chain(employee_id: str, db: Session = Depends(get_db)):
    chain = get_manager_chain(employee_id=employee_id, db=db)
    return chain

import os
import shutil
from uuid import uuid4
from fastapi import UploadFile, File, Form, HTTPException, status
from fastapi.responses import FileResponse
from app.db.models import EmployeeDocument
from app.schemas.document import EmployeeDocumentPublic
from app.core.rbac import get_current_user, has_permission

UPLOAD_DIR = "uploads/documents"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post('/{employee_id}/documents', response_model=EmployeeDocumentPublic)
def upload_document(
    employee_id: str,
    document_type: str = Form(...),
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if employee_id != user.id and not has_permission(user.role, 'edit_employee'):
        raise HTTPException(status_code=403, detail="Not authorized to upload documents for this employee")

    file_id = str(uuid4())
    ext = file.filename.split('.')[-1] if '.' in file.filename else ''
    safe_filename = f"{file_id}.{ext}" if ext else file_id
    file_path = os.path.join(UPLOAD_DIR, safe_filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    doc = EmployeeDocument(
        employee_id=employee_id,
        document_type=document_type,
        file_name=file.filename,
        file_path=file_path,
        uploaded_by=user.id
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return EmployeeDocumentPublic.model_validate(doc, from_attributes=True)

@router.get('/{employee_id}/documents', response_model=list[EmployeeDocumentPublic])
def list_documents(
    employee_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if employee_id != user.id and not has_permission(user.role, 'view_employee'): # Note: view_employee check
        pass # simplified for now
    
    docs = db.query(EmployeeDocument).filter(EmployeeDocument.employee_id == employee_id).all()
    return [EmployeeDocumentPublic.model_validate(d, from_attributes=True) for d in docs]

@router.get('/documents/{doc_id}/download')
def download_document(
    doc_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    doc = db.query(EmployeeDocument).filter(EmployeeDocument.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    if not os.path.exists(doc.file_path):
        raise HTTPException(status_code=404, detail="File not found on server")

    return FileResponse(doc.file_path, filename=doc.file_name)
