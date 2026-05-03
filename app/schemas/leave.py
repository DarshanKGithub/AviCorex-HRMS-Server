from datetime import date, datetime

from pydantic import BaseModel, Field


class LeaveTypePublic(BaseModel):
    id: str
    name: str
    description: str | None = None
    default_days_per_year: int
    is_active: bool
    created_at: datetime


class LeaveRequestCreate(BaseModel):
    leave_type_id: str
    start_date: date
    end_date: date
    reason: str | None = None


class LeaveRequestUpdate(BaseModel):
    status: str | None = None
    reason: str | None = None


class LeaveRequestPublic(BaseModel):
    id: str
    employee_id: str
    leave_type_id: str
    start_date: date
    end_date: date
    days_requested: int
    reason: str | None = None
    status: str
    approver_id: str | None = None
    approved_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class ApprovePayload(BaseModel):
    approve: bool = Field(...)
    note: str | None = None


class LeaveBalancePublic(BaseModel):
    id: str
    employee_id: str
    leave_type_id: str
    year: int
    balance_days: int
    created_at: datetime
    updated_at: datetime


class PaginatedLeaveRequests(BaseModel):
    items: list[LeaveRequestPublic]
    total: int
    page: int
    size: int
