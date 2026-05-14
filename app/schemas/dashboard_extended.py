"""Extended Dashboard schemas for My Space, Organization, Calendar, Delegation."""
from datetime import datetime, date
from pydantic import BaseModel
from typing import Optional, List


# ============================================================================
# MY SPACE - Personal Workspace Models
# ============================================================================

class ActivityLog(BaseModel):
    """Activity log entry for feeds."""
    id: str
    type: str  # 'leave_approved', 'task_completed', 'announcement', etc.
    title: str
    description: Optional[str] = None
    actor_name: str
    actor_avatar_url: Optional[str] = None
    timestamp: datetime
    icon: str  # e.g., 'check_circle', 'info', 'warning'
    color: str  # e.g., 'success', 'info', 'warning'
    action_url: Optional[str] = None

    class Config:
        from_attributes = True


class LeaveApproval(BaseModel):
    """Leave request pending approval."""
    id: str
    employee_name: str
    employee_id: str
    leave_type: str
    start_date: date
    end_date: date
    days: float
    reason: str
    status: str  # 'pending', 'approved', 'rejected'
    requested_at: datetime
    priority: str  # 'low', 'medium', 'high'

    class Config:
        from_attributes = True


class TimeLogEntry(BaseModel):
    """Time log entry."""
    id: str
    date: date
    check_in_time: Optional[datetime] = None
    check_out_time: Optional[datetime] = None
    worked_hours: Optional[float] = None
    status: str  # 'present', 'absent', 'late', 'half_day', 'work_from_home'
    notes: Optional[str] = None

    class Config:
        from_attributes = True


class MySpaceDashboard(BaseModel):
    """My Space (Personal) dashboard data."""
    employee_id: str
    full_name: str
    avatar_url: Optional[str] = None
    role: str
    department: Optional[str] = None
    email: str
    
    # Quick stats
    pending_leaves: int
    pending_approvals: int
    pending_tasks: int
    today_hours: float
    
    # Activities and feeds
    recent_activities: List[ActivityLog]
    pending_leave_approvals: List[LeaveApproval]
    recent_time_logs: List[TimeLogEntry]
    
    # Today's overview
    today_schedule: Optional[dict] = None
    today_attendance_status: Optional[str] = None

    class Config:
        from_attributes = True


# ============================================================================
# ORGANIZATION - Org-wide Dashboards
# ============================================================================

class DepartmentStat(BaseModel):
    """Department statistics."""
    department_id: str
    department_name: str
    total_employees: int
    active_employees: int
    leave_count: int
    pending_approvals: int
    average_attendance: float  # percentage

    class Config:
        from_attributes = True


class TeamMemberStatus(BaseModel):
    """Team member current status."""
    employee_id: str
    full_name: str
    avatar_url: Optional[str] = None
    role: str
    department: str
    status: str  # 'present', 'absent', 'on_leave', 'work_from_home'
    check_in_time: Optional[datetime] = None
    last_activity: Optional[datetime] = None

    class Config:
        from_attributes = True


class OrganizationDashboard(BaseModel):
    """Organization-wide dashboard."""
    generated_at: datetime
    
    # Overall stats
    total_employees: int
    active_today: int
    on_leave: int
    absent: int
    work_from_home: int
    
    # Department breakdown
    departments: List[DepartmentStat]
    
    # Team member statuses (for managers/admins)
    team_members: List[TeamMemberStatus]
    
    # Org-wide metrics
    average_attendance_rate: float
    pending_approvals_count: int
    pending_leaves: int
    pending_tasks: int

    class Config:
        from_attributes = True


# ============================================================================
# CALENDAR & EVENTS
# ============================================================================

class CalendarEvent(BaseModel):
    """Calendar event."""
    id: str
    title: str
    description: Optional[str] = None
    start_time: datetime
    end_time: datetime
    event_type: str  # 'meeting', 'deadline', 'holiday', 'birthday', 'leave', 'task'
    location: Optional[str] = None
    attendees: List[str] = []  # List of employee IDs or names
    organizer_id: Optional[str] = None
    color: str  # Event color for UI
    is_all_day: bool = False
    recurring: Optional[str] = None  # 'daily', 'weekly', 'monthly', None
    status: str = 'confirmed'  # 'confirmed', 'tentative', 'cancelled'
    reminder_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class CalendarResponse(BaseModel):
    """Calendar data for a date range."""
    start_date: date
    end_date: date
    events: List[CalendarEvent]
    holidays: List[dict]  # List of holidays in range

    class Config:
        from_attributes = True


# ============================================================================
# DELEGATION & TASKS
# ============================================================================

class DelegatedTask(BaseModel):
    """Delegated task."""
    id: str
    title: str
    description: Optional[str] = None
    delegated_by: str  # Employee who delegated
    delegated_to: str  # Employee who received
    due_date: date
    priority: str  # 'low', 'medium', 'high', 'urgent'
    status: str  # 'pending', 'in_progress', 'completed', 'cancelled'
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    notes: Optional[str] = None

    class Config:
        from_attributes = True


class DelegationDashboard(BaseModel):
    """Delegation & task management dashboard."""
    delegated_by_me: List[DelegatedTask]  # Tasks I've delegated
    delegated_to_me: List[DelegatedTask]  # Tasks delegated to me
    total_pending_tasks: int
    overdue_tasks: int
    completed_this_week: int
    completion_rate: float  # percentage

    class Config:
        from_attributes = True


# ============================================================================
# ACTIVITY FEED
# ============================================================================

class FeedItem(BaseModel):
    """Activity feed item."""
    id: str
    type: str  # 'announcement', 'leave_status', 'approval', 'task', 'milestone'
    title: str
    description: Optional[str] = None
    actor_id: str
    actor_name: str
    actor_avatar_url: Optional[str] = None
    timestamp: datetime
    category: str
    priority: str  # 'low', 'medium', 'high'
    icon: str
    color: str
    action_url: Optional[str] = None
    read: bool = False

    class Config:
        from_attributes = True


class ActivityFeedResponse(BaseModel):
    """Activity feed with pagination."""
    items: List[FeedItem]
    total_count: int
    page: int
    page_size: int
    has_more: bool

    class Config:
        from_attributes = True
