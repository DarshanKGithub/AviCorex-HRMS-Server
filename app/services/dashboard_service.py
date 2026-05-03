from datetime import date, datetime, timezone

from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from app.db.models import Department, Employee
from app.schemas.dashboard import (
    AttendanceSummary,
    DashboardFilters,
    DashboardKpis,
    DashboardSummaryResponse,
    DepartmentBreakdownItem,
)


def get_dashboard_summary(
    *,
    db: Session,
    start_date: date | None = None,
    end_date: date | None = None,
    department_id: str | None = None,
) -> DashboardSummaryResponse:
    filters = []
    if department_id:
        filters.append(Employee.department_id == department_id)

    total_stmt = select(func.count(Employee.id))
    active_stmt = select(func.count(Employee.id)).where(Employee.is_active.is_(True))
    inactive_stmt = select(func.count(Employee.id)).where(Employee.is_active.is_(False))

    for condition in filters:
        total_stmt = total_stmt.where(condition)
        active_stmt = active_stmt.where(condition)
        inactive_stmt = inactive_stmt.where(condition)

    total_employees = int(db.scalar(total_stmt) or 0)
    active_employees = int(db.scalar(active_stmt) or 0)
    inactive_employees = int(db.scalar(inactive_stmt) or 0)

    if department_id:
        departments_count = 1 if db.scalar(select(Department.id).where(Department.id == department_id)) else 0
    else:
        departments_count = int(db.scalar(select(func.count(Department.id))) or 0)

    active_sum = func.coalesce(
        func.sum(
            case(
                (Employee.is_active.is_(True), 1),
                else_=0,
            )
        ),
        0,
    )

    breakdown_stmt = (
        select(
            Department.id,
            Department.name,
            func.count(Employee.id),
            active_sum,
        )
        .select_from(Department)
        .outerjoin(Employee, Employee.department_id == Department.id)
        .group_by(Department.id, Department.name)
        .order_by(Department.name)
    )

    if department_id:
        breakdown_stmt = breakdown_stmt.where(Department.id == department_id)

    rows = db.execute(breakdown_stmt).all()
    department_breakdown: list[DepartmentBreakdownItem] = []
    for row in rows:
        total = int(row[2] or 0)
        active = int(row[3] or 0)
        department_breakdown.append(
            DepartmentBreakdownItem(
                department_id=row[0],
                department_name=row[1],
                total_employees=total,
                active_employees=active,
                inactive_employees=total - active,
            )
        )

    if not department_id:
        unassigned_total = int(db.scalar(select(func.count(Employee.id)).where(Employee.department_id.is_(None))) or 0)
        if unassigned_total > 0:
            unassigned_active = int(
                db.scalar(
                    select(func.count(Employee.id)).where(
                        Employee.department_id.is_(None),
                        Employee.is_active.is_(True),
                    )
                )
                or 0
            )
            department_breakdown.append(
                DepartmentBreakdownItem(
                    department_id=None,
                    department_name='Unassigned',
                    total_employees=unassigned_total,
                    active_employees=unassigned_active,
                    inactive_employees=unassigned_total - unassigned_active,
                )
            )

    return DashboardSummaryResponse(
        generated_at=datetime.now(timezone.utc),
        filters=DashboardFilters(
            start_date=start_date,
            end_date=end_date,
            department_id=department_id,
        ),
        kpis=DashboardKpis(
            total_employees=total_employees,
            active_employees=active_employees,
            inactive_employees=inactive_employees,
            departments_count=departments_count,
            pending_approvals=0,
        ),
        attendance_summary=AttendanceSummary(
            status='stubbed',
            present=0,
            absent=0,
            late=0,
        ),
        department_breakdown=department_breakdown,
    )
