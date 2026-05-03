from datetime import date, datetime

from pydantic import BaseModel


class DashboardFilters(BaseModel):
    start_date: date | None = None
    end_date: date | None = None
    department_id: str | None = None


class DashboardKpis(BaseModel):
    total_employees: int
    active_employees: int
    inactive_employees: int
    departments_count: int
    pending_approvals: int


class AttendanceSummary(BaseModel):
    status: str
    present: int
    absent: int
    late: int


class DepartmentBreakdownItem(BaseModel):
    department_id: str | None = None
    department_name: str
    total_employees: int
    active_employees: int
    inactive_employees: int


class DashboardSummaryResponse(BaseModel):
    generated_at: datetime
    filters: DashboardFilters
    kpis: DashboardKpis
    attendance_summary: AttendanceSummary
    department_breakdown: list[DepartmentBreakdownItem]
