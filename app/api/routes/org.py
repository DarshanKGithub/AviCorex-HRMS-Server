from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.organization import DepartmentCreate, DepartmentPublic, DesignationCreate, DesignationPublic
from app.services.org_service import list_departments, create_department, list_designations, create_designation
from app.services.auth_service import get_user_from_token

security = HTTPBearer(auto_error=False)

router = APIRouter()


@router.get('/departments', response_model=list[DepartmentPublic])
def departments(db: Session = Depends(get_db)):
    return [DepartmentPublic(id=d.id, name=d.name) for d in list_departments(db=db)]


@router.post('/departments', response_model=DepartmentPublic)
def create_dept(
    payload: DepartmentCreate,
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: Session = Depends(get_db),
) -> DepartmentPublic:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Not authenticated')

    user = get_user_from_token(credentials.credentials, db=db)
    if user.role not in ('Admin', 'HR'):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Insufficient privileges')

    d = create_department(payload=payload, db=db)
    return DepartmentPublic(id=d.id, name=d.name)


@router.get('/designations', response_model=list[DesignationPublic])
def designations(db: Session = Depends(get_db)):
    return [DesignationPublic(id=d.id, name=d.name) for d in list_designations(db=db)]


@router.post('/designations', response_model=DesignationPublic)
def create_des(
    payload: DesignationCreate,
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: Session = Depends(get_db),
) -> DesignationPublic:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Not authenticated')

    user = get_user_from_token(credentials.credentials, db=db)
    if user.role not in ('Admin', 'HR'):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Insufficient privileges')

    d = create_designation(payload=payload, db=db)
    return DesignationPublic(id=d.id, name=d.name)
