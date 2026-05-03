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
