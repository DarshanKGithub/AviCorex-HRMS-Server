from pydantic import BaseModel, Field
from typing import Literal


class DepartmentCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)


class DepartmentPublic(BaseModel):
    id: str
    name: str


class DesignationCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)


class DesignationPublic(BaseModel):
    id: str
    name: str

class OrgNode(BaseModel):
    id: str
    full_name: str
    designation: str | None = None
    department: str | None = None
    manager_id: str | None = None
    children: list['OrgNode'] = []
