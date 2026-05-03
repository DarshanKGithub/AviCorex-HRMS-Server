from pydantic import BaseModel, Field
from typing import Literal


class EmployeeCreate(BaseModel):
    full_name: str = Field(min_length=1, max_length=120)
    email: str
    department_id: str | None = None
    designation_id: str | None = None
    manager_id: str | None = None


class EmployeeUpdate(BaseModel):
    full_name: str | None = None
    department_id: str | None = None
    designation_id: str | None = None
    manager_id: str | None = None
    is_active: bool | None = None


class EmployeePublic(BaseModel):
    id: str
    full_name: str
    email: str
    department_id: str | None = None
    designation_id: str | None = None
    manager_id: str | None = None
    is_active: bool


class PaginatedEmployees(BaseModel):
    items: list[EmployeePublic]
    total: int
    page: int
    size: int
