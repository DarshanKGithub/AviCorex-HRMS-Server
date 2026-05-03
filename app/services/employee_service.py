from typing import List, Tuple
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from uuid import uuid4
from sqlalchemy import text

from app.db.models import Employee
from app.schemas.employee import EmployeeCreate, EmployeeUpdate


def list_employees(db: Session) -> List[Employee]:
    return db.scalars(select(Employee).order_by(Employee.full_name)).all()


def search_employees(db: Session, page: int = 1, size: int = 20, q: str | None = None,
                     department_id: str | None = None, designation_id: str | None = None) -> Tuple[List[Employee], int]:
    """Return (items, total) for employees matching optional filters with pagination."""
    stmt = select(Employee)
    filters = []
    if q:
        like = f"%{q.lower()}%"
        filters.append(func.lower(Employee.full_name).like(like) | func.lower(Employee.email).like(like))
    if department_id:
        filters.append(Employee.department_id == department_id)
    if designation_id:
        filters.append(Employee.designation_id == designation_id)

    if filters:
        for f in filters:
            stmt = stmt.where(f)

    total = db.scalar(select(func.count()).select_from(stmt.subquery()))

    items = db.scalars(stmt.order_by(Employee.full_name).offset((page - 1) * size).limit(size)).all()
    return items, int(total or 0)


def get_employee(employee_id: str, db: Session) -> Employee:
    emp = db.scalar(select(Employee).where(Employee.id == employee_id))
    if not emp:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Employee not found')
    return emp


def create_employee(payload: EmployeeCreate, db: Session, actor_id: str | None = None) -> Employee:
    existing = db.scalar(select(Employee).where(Employee.email == payload.email))
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Employee with this email exists')
    # validate manager exists if provided and prevent cycles
    new_id = str(uuid4())
    if payload.manager_id:
        mgr = db.scalar(select(Employee).where(Employee.id == payload.manager_id))
        if not mgr:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Manager not found')

        # walk up manager chain to ensure we don't encounter the new id (would create a cycle)
        current = payload.manager_id
        seen = set()
        while current:
            if current in seen:
                break
            seen.add(current)
            if current == new_id:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Manager assignment would create a cycle')
            current = db.scalar(select(Employee.manager_id).where(Employee.id == current))

    emp = Employee(
        id=new_id,
        full_name=payload.full_name,
        email=payload.email.lower(),
        department_id=payload.department_id,
        designation_id=payload.designation_id,
        manager_id=payload.manager_id,
    )
    db.add(emp)
    db.commit()
    db.refresh(emp)
    # audit
    try:
        from app.db.models import AuditLog
        db.add(AuditLog(actor_id=actor_id, action='create', object_type='employee', object_id=emp.id, data=str({'full_name': emp.full_name, 'email': emp.email})))
        db.commit()
    except Exception:
        db.rollback()
    return emp


def update_employee(employee_id: str, payload: EmployeeUpdate, db: Session, actor_id: str | None = None) -> Employee:
    emp = get_employee(employee_id, db)
    if payload.full_name is not None:
        emp.full_name = payload.full_name
    if payload.department_id is not None:
        emp.department_id = payload.department_id
    if payload.designation_id is not None:
        emp.designation_id = payload.designation_id
    if payload.manager_id is not None:
        # manager must exist
        if payload.manager_id == emp.id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Employee cannot be their own manager')

        mgr = None
        if payload.manager_id:
            mgr = db.scalar(select(Employee).where(Employee.id == payload.manager_id))
            if not mgr:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Manager not found')

        # detect cycles: walk up manager chain to ensure employee_id is not encountered
        current = payload.manager_id
        seen = set()
        while current:
            if current in seen:
                break
            seen.add(current)
            if current == emp.id:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Manager assignment would create a cycle')
            current = db.scalar(select(Employee.manager_id).where(Employee.id == current))

        emp.manager_id = payload.manager_id
    if payload.is_active is not None:
        emp.is_active = payload.is_active

    db.commit()
    db.refresh(emp)
    # audit
    try:
        from app.db.models import AuditLog
        db.add(AuditLog(actor_id=actor_id, action='update', object_type='employee', object_id=emp.id, data=str({'full_name': emp.full_name, 'email': emp.email})))
        db.commit()
    except Exception:
        db.rollback()
    return emp


def delete_employee(employee_id: str, db: Session, actor_id: str | None = None) -> None:
    emp = get_employee(employee_id, db)
    try:
        # record audit before delete
        from app.db.models import AuditLog
        db.add(AuditLog(actor_id=actor_id, action='delete', object_type='employee', object_id=emp.id, data=str({'full_name': emp.full_name, 'email': emp.email})))
        db.delete(emp)
        db.commit()
    except Exception:
        db.rollback()


def get_manager_chain(employee_id: str, db: Session) -> List[dict]:
    """Return manager chain for the given employee id as list of dicts (closest manager first)."""
    # get immediate manager
    emp = db.scalar(select(Employee).where(Employee.id == employee_id))
    if not emp:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Employee not found')

    start_mgr = emp.manager_id
    if not start_mgr:
        return []

    # Recursive CTE to walk manager chain upwards
    sql = text(
        "WITH RECURSIVE chain AS ("
        " SELECT id, full_name, email, manager_id FROM employees WHERE id = :start"
        " UNION ALL"
        " SELECT e.id, e.full_name, e.email, e.manager_id FROM employees e JOIN chain c ON e.id = c.manager_id"
        " ) SELECT id, full_name, email, manager_id FROM chain;"
    )

    result = db.execute(sql, {"start": start_mgr}).fetchall()
    # result is list of Row; convert to dicts
    chain = []
    for row in result:
        # skip the starter if it's empty? keep all starting from manager
        chain.append({"id": row[0], "full_name": row[1], "email": row[2], "manager_id": row[3]})
    return chain
