from datetime import date, datetime, time

from pydantic import BaseModel


# --- Shift Schemas ---
class ShiftBase(BaseModel):
    name: str
    start_time: time
    end_time: time
    grace_period_minutes: int = 0
    is_active: bool = True


class ShiftCreate(ShiftBase):
    pass


class ShiftUpdate(BaseModel):
    name: str | None = None
    start_time: time | None = None
    end_time: time | None = None
    grace_period_minutes: int | None = None
    is_active: bool | None = None


class ShiftPublic(ShiftBase):
    id: str
    created_at: datetime


class PaginatedShifts(BaseModel):
    items: list[ShiftPublic]
    total: int
    page: int
    size: int


# --- Employee Shift Assignment Schemas ---
class EmployeeShiftAssignmentBase(BaseModel):
    employee_id: str
    shift_id: str
    start_date: date
    end_date: date | None = None
    is_active: bool = True


class EmployeeShiftAssignmentCreate(EmployeeShiftAssignmentBase):
    pass


class EmployeeShiftAssignmentUpdate(BaseModel):
    shift_id: str | None = None
    end_date: date | None = None
    is_active: bool | None = None


class EmployeeShiftAssignmentPublic(EmployeeShiftAssignmentBase):
    id: str
    created_at: datetime


class PaginatedEmployeeShiftAssignments(BaseModel):
    items: list[EmployeeShiftAssignmentPublic]
    total: int
    page: int
    size: int


# --- Attendance Schemas ---
class AttendanceBase(BaseModel):
    employee_id: str
    attendance_date: date
    check_in_time: datetime | None = None
    check_out_time: datetime | None = None
    status: str  # present, absent, half-day, work-from-home
    is_late: bool = False
    late_minutes: int = 0
    is_half_day: bool = False
    is_work_from_home: bool = False
    notes: str | None = None


class AttendanceCreate(BaseModel):
    employee_id: str
    attendance_date: date
    check_in_time: datetime | None = None
    check_out_time: datetime | None = None
    is_work_from_home: bool = False
    notes: str | None = None


class AttendanceUpdate(BaseModel):
    check_in_time: datetime | None = None
    check_out_time: datetime | None = None
    status: str | None = None
    is_work_from_home: bool | None = None
    notes: str | None = None


class CheckInRequest(BaseModel):
    employee_id: str
    attendance_date: date
    check_in_time: datetime | None = None


class CheckOutRequest(BaseModel):
    employee_id: str
    attendance_date: date
    check_out_time: datetime | None = None


class AttendancePublic(AttendanceBase):
    id: str
    created_at: datetime
    updated_at: datetime


class PaginatedAttendance(BaseModel):
    items: list[AttendancePublic]
    total: int
    page: int
    size: int


# --- Attendance Rule Schemas ---
class AttendanceRuleBase(BaseModel):
    name: str
    rule_type: str  # late_entry, early_exit, half_day, etc.
    threshold_minutes: int
    is_active: bool = True


class AttendanceRuleCreate(AttendanceRuleBase):
    pass


class AttendanceRuleUpdate(BaseModel):
    name: str | None = None
    threshold_minutes: int | None = None
    is_active: bool | None = None


class AttendanceRulePublic(AttendanceRuleBase):
    id: str
    created_at: datetime


class PaginatedAttendanceRules(BaseModel):
    items: list[AttendanceRulePublic]
    total: int
    page: int
    size: int


# --- Attendance Summary Schemas ---
class AttendanceSummaryItem(BaseModel):
    date: date
    status: str
    check_in_time: datetime | None = None
    check_out_time: datetime | None = None
    is_late: bool
    is_half_day: bool
    is_work_from_home: bool


class EmployeeAttendanceSummary(BaseModel):
    employee_id: str
    start_date: date
    end_date: date
    total_days: int
    present_days: int
    absent_days: int
    half_days: int
    work_from_home_days: int
    late_days: int
    records: list[AttendanceSummaryItem]
