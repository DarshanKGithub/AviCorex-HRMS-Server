from typing import Optional
from sqlalchemy.orm import Session
from datetime import datetime
from app.db.models import TodoItem
from app.schemas.todo import TodoCreate, TodoUpdate


def create_todo(db: Session, employee_id: str, payload: TodoCreate) -> TodoItem:
    todo = TodoItem(
        employee_id=employee_id,
        title=payload.title,
        description=payload.description,
        due_date=payload.due_date,
        status='open',
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(todo)
    db.commit()
    db.refresh(todo)
    return todo


def list_todos(db: Session, employee_id: str, limit: int = 50, offset: int = 0):
    q = db.query(TodoItem).filter(TodoItem.employee_id == employee_id)
    total = q.count()
    items = q.order_by(TodoItem.created_at.desc()).limit(limit).offset(offset).all()
    return items, total


def get_todo(db: Session, todo_id: str) -> Optional[TodoItem]:
    return db.query(TodoItem).filter(TodoItem.id == todo_id).first()


def update_todo(db: Session, todo: TodoItem, payload: TodoUpdate) -> TodoItem:
    if payload.title is not None:
        todo.title = payload.title
    if payload.description is not None:
        todo.description = payload.description
    if payload.status is not None:
        todo.status = payload.status
    if payload.due_date is not None:
        todo.due_date = payload.due_date
    todo.updated_at = datetime.utcnow()
    db.add(todo)
    db.commit()
    db.refresh(todo)
    return todo


def delete_todo(db: Session, todo: TodoItem) -> None:
    db.delete(todo)
    db.commit()
