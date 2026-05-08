from __future__ import annotations
from typing import Optional
from pydantic import BaseModel
from datetime import date

class TodoCreate(BaseModel):
    title: str
    description: Optional[str] = None
    due_date: Optional[date] = None

class TodoUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    due_date: Optional[date] = None

class TodoPublic(BaseModel):
    id: str
    employee_id: str
    title: str
    description: Optional[str] = None
    status: str
    due_date: Optional[date] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

class PaginatedTodos(BaseModel):
    items: list[TodoPublic]
    total: int
    page: int
    size: int
