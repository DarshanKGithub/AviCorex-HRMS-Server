from datetime import date, datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict


class TimesheetBase(BaseModel):
    employee_id: str
    date: date
    project_id: Optional[str] = None
    task_description: str
    hours_worked: float
    status: Optional[str] = 'Draft'


class TimesheetCreate(TimesheetBase):
    pass


class TimesheetPublic(TimesheetBase):
    model_config = ConfigDict(from_attributes=True)
    id: str
    approver_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class OvertimeRequestBase(BaseModel):
    employee_id: str
    attendance_id: Optional[str] = None
    date: date
    hours: float
    reason: Optional[str] = None


class OvertimeRequestCreate(OvertimeRequestBase):
    pass


class OvertimeRequestPublic(OvertimeRequestBase):
    model_config = ConfigDict(from_attributes=True)
    id: str
    status: str
    approver_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class AttendanceRegularizationBase(BaseModel):
    employee_id: str
    attendance_id: Optional[str] = None
    date: date
    reason: str
    requested_check_in: Optional[datetime] = None
    requested_check_out: Optional[datetime] = None


class AttendanceRegularizationCreate(AttendanceRegularizationBase):
    pass


class AttendanceRegularizationPublic(AttendanceRegularizationBase):
    model_config = ConfigDict(from_attributes=True)
    id: str
    status: str
    approver_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class CompOffRequestBase(BaseModel):
    employee_id: str
    worked_date: date
    reason: Optional[str] = None


class CompOffRequestCreate(CompOffRequestBase):
    pass


class CompOffRequestPublic(CompOffRequestBase):
    model_config = ConfigDict(from_attributes=True)
    id: str
    status: str
    leave_balance_id: Optional[str] = None
    approver_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class BiometricDeviceBase(BaseModel):
    device_id: str
    name: str
    location: Optional[str] = None
    ip_address: Optional[str] = None
    status: Optional[str] = 'Active'


class BiometricDeviceCreate(BiometricDeviceBase):
    pass


class BiometricDevicePublic(BiometricDeviceBase):
    model_config = ConfigDict(from_attributes=True)
    id: str
    last_sync_time: Optional[datetime] = None
    created_at: datetime


class BiometricLogBase(BaseModel):
    device_id: str
    employee_id: str
    timestamp: datetime
    log_type: str


class BiometricLogCreate(BiometricLogBase):
    pass


class BiometricLogPublic(BiometricLogBase):
    model_config = ConfigDict(from_attributes=True)
    id: str
    status: str
    created_at: datetime


class RosterBase(BaseModel):
    name: str
    start_date: date
    end_date: date
    is_published: Optional[bool] = False


class RosterCreate(RosterBase):
    pass


class RosterPublic(RosterBase):
    model_config = ConfigDict(from_attributes=True)
    id: str
    created_at: datetime


class RosterEntryBase(BaseModel):
    roster_id: str
    employee_id: str
    date: date
    shift_id: Optional[str] = None
    is_off_day: Optional[bool] = False


class RosterEntryCreate(RosterEntryBase):
    pass


class RosterEntryPublic(RosterEntryBase):
    model_config = ConfigDict(from_attributes=True)
    id: str
    created_at: datetime


class PaginatedAttendanceRegularizations(BaseModel):
    items: List[AttendanceRegularizationPublic]
    total: int
    page: int
    size: int


class PaginatedTimesheets(BaseModel):
    items: List[TimesheetPublic]
    total: int
    page: int
    size: int


class PaginatedOvertimeRequests(BaseModel):
    items: List[OvertimeRequestPublic]
    total: int
    page: int
    size: int


class PaginatedCompOffRequests(BaseModel):
    items: List[CompOffRequestPublic]
    total: int
    page: int
    size: int
