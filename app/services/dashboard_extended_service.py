"""Extended dashboard service for My Space, Organization, Calendar, Delegation."""
from datetime import datetime, date, timedelta, timezone
from sqlalchemy.orm import Session
from sqlalchemy import select, func, and_, or_, case, Integer

from app.db.models import Employee, LeaveRequest, LeaveBalance, Attendance, User, Department, Shift, Holiday, TodoItem
from app.schemas.dashboard_extended import (
    MySpaceDashboard, OrganizationDashboard, CalendarResponse, DelegationDashboard,
    ActivityLog, LeaveApproval, TimeLogEntry, DepartmentStat, TeamMemberStatus,
    CalendarEvent, FeedItem, ActivityFeedResponse
)


def _leave_timestamp(leave_request: LeaveRequest) -> datetime:
    """Return the best available timestamp for a leave request."""

    if leave_request.approved_at:
        return leave_request.approved_at

    return datetime.combine(leave_request.start_date, datetime.min.time())


def get_my_space_dashboard(
    *,
    db: Session,
    employee_id: str,
) -> MySpaceDashboard:
    """Get personalized My Space dashboard for an employee."""
    
    # Get employee
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise ValueError(f"Employee {employee_id} not found")
    
    user = db.query(User).filter(User.id == employee_id).first()
    department = None
    if employee.department_id:
        department = db.query(Department).filter(Department.id == employee.department_id).first()
    
    # Get pending leaves
    today = date.today()
    pending_leaves_stmt = select(func.count(LeaveRequest.id)).where(
        and_(
            LeaveRequest.employee_id == employee_id,
            LeaveRequest.status == 'pending'
        )
    )
    pending_leaves = int(db.scalar(pending_leaves_stmt) or 0)
    
    # Get recent activities (from todos, leave requests, etc.)
    recent_activities = []
    
    # Leave request updates
    leave_requests = db.query(LeaveRequest).filter(
        LeaveRequest.employee_id == employee_id
    ).order_by(LeaveRequest.approved_at.desc().nullslast(), LeaveRequest.start_date.desc()).limit(3).all()
    
    for leave_req in leave_requests:
        recent_activities.append(ActivityLog(
            id=leave_req.id,
            type='leave_request',
            title=f'{leave_req.status.title()} - {leave_req.leave_type.name if leave_req.leave_type else "Leave"}',
            description=f'Leave from {leave_req.start_date} to {leave_req.end_date}',
            actor_name=employee.full_name,
            timestamp=_leave_timestamp(leave_req),
            icon='check_circle' if leave_req.status == 'approved' else 'schedule',
            color='success' if leave_req.status == 'approved' else 'info',
        ))
    
    # Get pending leave approvals (if manager/HR)
    pending_leave_approvals = []
    if user and user.role in ['Manager', 'HR', 'Admin']:
        # Get all pending leaves from team
        pending_leaves_query = db.query(LeaveRequest).filter(
            LeaveRequest.status == 'pending'
        ).order_by(LeaveRequest.start_date.desc()).limit(5).all()
        
        for leave_req in pending_leaves_query:
            leave_emp = db.query(Employee).filter(Employee.id == leave_req.employee_id).first()
            pending_leave_approvals.append(LeaveApproval(
                id=leave_req.id,
                employee_name=leave_emp.full_name if leave_emp else 'Unknown',
                employee_id=leave_req.employee_id,
                leave_type=leave_req.leave_type.name if leave_req.leave_type else 'Leave',
                start_date=leave_req.start_date,
                end_date=leave_req.end_date,
                days=leave_req.number_of_days,
                reason=leave_req.reason or '',
                status=leave_req.status,
                requested_at=_leave_timestamp(leave_req),
                priority='high' if (leave_req.start_date - today).days <= 2 else 'medium',
            ))
    
    # Get recent time logs
    recent_time_logs = []
    recent_attendance = db.query(Attendance).filter(
        Attendance.employee_id == employee_id
    ).order_by(Attendance.attendance_date.desc()).limit(7).all()
    
    for att in recent_attendance:
        worked_hours = None
        if att.check_in_time and att.check_out_time:
            delta = att.check_out_time - att.check_in_time
            worked_hours = round(delta.total_seconds() / 3600, 2)
        
        recent_time_logs.append(TimeLogEntry(
            id=att.id,
            date=att.attendance_date,
            check_in_time=att.check_in_time,
            check_out_time=att.check_out_time,
            worked_hours=worked_hours,
            status='present' if att.check_in_time else 'absent',
        ))
    
    # Get today's attendance
    today_attendance = db.query(Attendance).filter(
        and_(
            Attendance.employee_id == employee_id,
            Attendance.attendance_date == today
        )
    ).first()
    
    today_hours = 0.0
    if today_attendance and today_attendance.check_in_time and today_attendance.check_out_time:
        delta = today_attendance.check_out_time - today_attendance.check_in_time
        today_hours = round(delta.total_seconds() / 3600, 2)
    elif today_attendance and today_attendance.check_in_time:
        # Still checked in, calculate from check-in to now
        delta = datetime.now(timezone.utc).replace(tzinfo=None) - today_attendance.check_in_time.replace(tzinfo=None)
        today_hours = round(delta.total_seconds() / 3600, 2)
    
    return MySpaceDashboard(
        employee_id=employee_id,
        full_name=employee.full_name,
        avatar_url=getattr(employee, 'avatar_url', None),
        role=user.role if user else 'Employee',
        department=department.name if department else None,
        email=user.email if user else '',
        pending_leaves=pending_leaves,
        pending_approvals=len(pending_leave_approvals),
        pending_tasks=0,  # TODO: Implement tasks system
        today_hours=today_hours,
        recent_activities=recent_activities[:5],
        pending_leave_approvals=pending_leave_approvals,
        recent_time_logs=recent_time_logs[:7],
        today_attendance_status=today_attendance.status if today_attendance else None,
    )


def get_organization_dashboard(
    *,
    db: Session,
) -> OrganizationDashboard:
    """Get organization-wide dashboard."""
    
    today = date.today()
    
    # Get total employees
    total_employees = int(db.scalar(select(func.count(Employee.id))) or 0)
    
    # Get today's attendance stats
    today_attendance = db.query(Attendance).filter(
        Attendance.attendance_date == today
    ).all()
    
    present = sum(1 for a in today_attendance if a.check_in_time)
    absent = sum(1 for a in today_attendance if not a.check_in_time and a.attendance_date == today)
    
    # Get on-leave count
    on_leave = db.query(LeaveRequest).filter(
        and_(
            LeaveRequest.start_date <= today,
            LeaveRequest.end_date >= today,
            LeaveRequest.status == 'approved'
        )
    ).count()
    
    active_today = present
    work_from_home = 0  # TODO: Implement WFH tracking
    
    # Department breakdown
    departments = []
    dept_rows = db.query(
        Department.id,
        Department.name,
        func.count(Employee.id),
        func.sum(case((Employee.is_active.is_(True), 1), else_=0))
    ).outerjoin(Employee, Employee.department_id == Department.id).group_by(Department.id, Department.name).all()
    
    for dept_id, dept_name, total, active in dept_rows:
        departments.append(DepartmentStat(
            department_id=dept_id,
            department_name=dept_name,
            total_employees=int(total or 0),
            active_employees=int(active or 0),
            leave_count=0,  # TODO: Calculate
            pending_approvals=0,  # TODO: Calculate
            average_attendance=80.0,  # TODO: Calculate from attendance records
        ))
    
    # Get team member statuses (first 50)
    employees = db.query(Employee).limit(50).all()
    team_members = []
    
    for emp in employees:
        emp_attendance = db.query(Attendance).filter(
            and_(
                Attendance.employee_id == emp.id,
                Attendance.attendance_date == today
            )
        ).first()

        emp_department = None
        if emp.department_id:
            emp_department = db.query(Department).filter(Department.id == emp.department_id).first()
        
        status = 'absent'
        check_in_time = None
        if emp_attendance and emp_attendance.check_in_time:
            status = 'present'
            check_in_time = emp_attendance.check_in_time
        
        team_members.append(TeamMemberStatus(
            employee_id=emp.id,
            full_name=emp.full_name,
            avatar_url=getattr(emp, 'avatar_url', None),
            role=getattr(db.query(User).filter(User.id == emp.id).first(), 'role', 'Employee'),
            department=emp_department.name if emp_department else 'Unassigned',
            status=status,
            check_in_time=check_in_time,
            last_activity=check_in_time,
        ))
    
    # Pending approvals
    pending_approvals = db.query(LeaveRequest).filter(
        LeaveRequest.status == 'pending'
    ).count()
    
    avg_attendance = (present / max(total_employees, 1)) * 100 if total_employees > 0 else 0
    
    return OrganizationDashboard(
        generated_at=datetime.now(timezone.utc),
        total_employees=total_employees,
        active_today=active_today,
        on_leave=on_leave,
        absent=absent,
        work_from_home=work_from_home,
        departments=departments,
        team_members=team_members,
        average_attendance_rate=round(avg_attendance, 1),
        pending_approvals_count=pending_approvals,
        pending_leaves=on_leave,
        pending_tasks=0,
    )


def get_calendar_events(
    *,
    db: Session,
    employee_id: str,
    start_date: date,
    end_date: date,
) -> CalendarResponse:
    """Get calendar events for a date range."""
    
    events = []
    
    # Get holidays in range
    holidays = db.query(Holiday).filter(
        and_(
            Holiday.holiday_date >= start_date,
            Holiday.holiday_date <= end_date
        )
    ).all()
    
    holiday_list = []
    for holiday in holidays:
        events.append(CalendarEvent(
            id=holiday.id,
            title=holiday.name,
            start_time=datetime.combine(holiday.holiday_date, datetime.min.time()),
            end_time=datetime.combine(holiday.holiday_date, datetime.max.time()),
            event_type='holiday',
            is_all_day=True,
            color='#ff6b6b',
        ))
        holiday_list.append({
            'date': str(holiday.holiday_date),
            'name': holiday.name,
        })
    
    # Get approved leaves for employee
    leaves = db.query(LeaveRequest).filter(
        and_(
            LeaveRequest.employee_id == employee_id,
            LeaveRequest.start_date <= end_date,
            LeaveRequest.end_date >= start_date,
            LeaveRequest.status == 'approved'
        )
    ).all()
    
    for leave in leaves:
        events.append(CalendarEvent(
            id=leave.id,
            title=f'{leave.leave_type.name if leave.leave_type else "Leave"}',
            start_time=datetime.combine(leave.start_date, datetime.min.time()),
            end_time=datetime.combine(leave.end_date, datetime.max.time()),
            event_type='leave',
            is_all_day=True,
            color='#4dabf7',
            description=leave.reason,
        ))
    
    return CalendarResponse(
        start_date=start_date,
        end_date=end_date,
        events=events,
        holidays=holiday_list,
    )


def get_delegation_dashboard(
    *,
    db: Session,
    employee_id: str,
) -> DelegationDashboard:
    """Get delegation and task dashboard."""
    
    # TODO: Implement when tasks table is added to models
    # For now, return empty dashboard
    
    return DelegationDashboard(
        delegated_by_me=[],
        delegated_to_me=[],
        total_pending_tasks=0,
        overdue_tasks=0,
        completed_this_week=0,
        completion_rate=0.0,
    )


def get_activity_feed(
    *,
    db: Session,
    employee_id: str,
    page: int = 1,
    page_size: int = 20,
) -> ActivityFeedResponse:
    """Get activity feed for employee."""
    
    items = []
    
    # Get recent leave request activity
    recent_leaves = db.query(LeaveRequest).filter(
        LeaveRequest.employee_id == employee_id
    ).order_by(LeaveRequest.approved_at.desc().nullslast(), LeaveRequest.start_date.desc()).limit(page_size).all()
    
    for leave in recent_leaves:
        icon_map = {
            'pending': 'schedule',
            'approved': 'check_circle',
            'rejected': 'cancel',
        }
        color_map = {
            'pending': 'warning',
            'approved': 'success',
            'rejected': 'error',
        }
        
        items.append(FeedItem(
            id=f'leave_{leave.id}',
            type='leave_status',
            title=f'Leave Request {leave.status.title()}',
            description=f'{leave.leave_type.name if leave.leave_type else "Leave"} from {leave.start_date} to {leave.end_date}',
            actor_id=employee_id,
            actor_name='You',
            timestamp=_leave_timestamp(leave),
            category='leave',
            priority='high' if leave.status == 'pending' else 'medium',
            icon=icon_map.get(leave.status, 'info'),
            color=color_map.get(leave.status, 'info'),
            action_url=f'/leaves',
        ))
    
    # Get attendance activity
    recent_attendance = db.query(Attendance).filter(
        Attendance.employee_id == employee_id
    ).order_by(Attendance.attendance_date.desc()).limit(5).all()
    
    for att in recent_attendance:
        items.append(FeedItem(
            id=f'attendance_{att.id}',
            type='attendance',
            title='Attendance Recorded',
            description=f'Checked in at {att.check_in_time.strftime("%H:%M") if att.check_in_time else "N/A"}',
            actor_id=employee_id,
            actor_name='System',
            timestamp=att.check_in_time or datetime.now(timezone.utc),
            category='attendance',
            priority='low',
            icon='check_circle',
            color='success',
            action_url=f'/attendance',
        ))
    
    # Sort by timestamp descending
    items.sort(key=lambda x: x.timestamp, reverse=True)
    
    # Pagination
    total_count = len(items)
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    paginated_items = items[start_idx:end_idx]
    
    return ActivityFeedResponse(
        items=paginated_items,
        total_count=total_count,
        page=page,
        page_size=page_size,
        has_more=end_idx < total_count,
    )
