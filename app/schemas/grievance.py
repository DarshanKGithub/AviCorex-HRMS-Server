from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class EmployeeGrievanceBase(BaseModel):
    against_employee_id: Optional[str] = None
    subject: str
    description: str


class EmployeeGrievanceCreate(EmployeeGrievanceBase):
    pass


class EmployeeGrievanceStatusUpdate(BaseModel):
    status: str = Field(..., description="New status: Submitted, Investigating, Resolved")

class GrievanceInvestigationUpdate(BaseModel):
    investigator_id: Optional[str] = None
    investigation_notes: Optional[str] = None
    meeting_scheduled_at: Optional[datetime] = None
    status: Optional[str] = None


class EmployeeGrievancePublic(EmployeeGrievanceBase):
    id: str
    employee_id: str
    status: str
    investigator_id: Optional[str] = None
    investigation_notes: Optional[str] = None
    meeting_scheduled_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class PaginatedEmployeeGrievances(BaseModel):
    items: List[EmployeeGrievancePublic]
    total: int
    page: int
    size: int
