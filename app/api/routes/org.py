from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.rbac import require_permissions, get_current_user
from app.db.database import get_db
from app.db.models import User
from app.schemas.organization import DepartmentCreate, DepartmentPublic, DesignationCreate, DesignationPublic, OrgNode
from app.services.org_service import list_departments, create_department, list_designations, create_designation, get_org_hierarchy

router = APIRouter()


@router.get('/departments', response_model=list[DepartmentPublic])
def departments(db: Session = Depends(get_db)):
    return [DepartmentPublic(id=d.id, name=d.name) for d in list_departments(db=db)]


@router.post('/departments', response_model=DepartmentPublic)
def create_dept(
    payload: DepartmentCreate,
    _user: User = Depends(require_permissions('manage_org')),
    db: Session = Depends(get_db),
) -> DepartmentPublic:
    d = create_department(payload=payload, db=db)
    return DepartmentPublic(id=d.id, name=d.name)


@router.get('/designations', response_model=list[DesignationPublic])
def designations(db: Session = Depends(get_db)):
    return [DesignationPublic(id=d.id, name=d.name) for d in list_designations(db=db)]


@router.post('/designations', response_model=DesignationPublic)
def create_des(
    payload: DesignationCreate,
    _user: User = Depends(require_permissions('manage_org')),
    db: Session = Depends(get_db),
) -> DesignationPublic:
    d = create_designation(payload=payload, db=db)
    return DesignationPublic(id=d.id, name=d.name)


@router.get('/hierarchy', response_model=list[OrgNode])
def get_hierarchy(
    _user: User = Depends(get_current_user), # Just basic auth for now
    db: Session = Depends(get_db),
):
    return get_org_hierarchy(db)
