from typing import List
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Department, Designation
from app.schemas.organization import DepartmentCreate, DesignationCreate
from fastapi import HTTPException, status


def list_departments(db: Session) -> List[Department]:
    return db.scalars(select(Department).order_by(Department.name)).all()


def create_department(payload: DepartmentCreate, db: Session) -> Department:
    existing = db.scalar(select(Department).where(Department.name == payload.name))
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Department already exists')
    dept = Department(name=payload.name)
    db.add(dept)
    db.commit()
    db.refresh(dept)
    return dept


def list_designations(db: Session) -> List[Designation]:
    return db.scalars(select(Designation).order_by(Designation.name)).all()


def create_designation(payload: DesignationCreate, db: Session) -> Designation:
    existing = db.scalar(select(Designation).where(Designation.name == payload.name))
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Designation already exists')
    des = Designation(name=payload.name)
    db.add(des)
    db.commit()
    db.refresh(des)
    return des
