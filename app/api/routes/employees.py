from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.employee import EmployeeCreate, EmployeePublic, EmployeeUpdate, PaginatedEmployees
from app.services.employee_service import list_employees, search_employees, create_employee, get_employee, update_employee, delete_employee
from app.services.employee_service import get_manager_chain
from app.services.auth_service import get_user_from_token

security = HTTPBearer(auto_error=False)

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
def create(payload: EmployeeCreate, credentials: HTTPAuthorizationCredentials | None = Depends(security), db: Session = Depends(get_db)):
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Not authenticated')

    user = get_user_from_token(credentials.credentials, db=db)
    if user.role not in ('Admin', 'HR'):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Insufficient privileges')

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
def patch(employee_id: str, payload: EmployeeUpdate, credentials: HTTPAuthorizationCredentials | None = Depends(security), db: Session = Depends(get_db)):
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Not authenticated')

    user = get_user_from_token(credentials.credentials, db=db)
    if user.role not in ('Admin', 'HR'):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Insufficient privileges')

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
def remove(employee_id: str, credentials: HTTPAuthorizationCredentials | None = Depends(security), db: Session = Depends(get_db)):
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Not authenticated')

    user = get_user_from_token(credentials.credentials, db=db)
    if user.role not in ('Admin', 'HR'):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Insufficient privileges')

    delete_employee(employee_id, db=db, actor_id=user.id)
    return {'detail': 'deleted'}


@router.get('/{employee_id}/manager-chain')
def manager_chain(employee_id: str, db: Session = Depends(get_db)):
    chain = get_manager_chain(employee_id=employee_id, db=db)
    return chain
