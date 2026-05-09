from pydantic import BaseModel, Field
from typing import Optional
from datetime import date, datetime

# ==================== GOAL SCHEMAS ====================

class GoalBase(BaseModel):
    title: str = Field(..., min_length=3, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    status: str = Field(default='Active')  # Active, Paused, Completed, Cancelled
    start_date: date
    end_date: date
    target_value: Optional[float] = None
    achieved_value: Optional[float] = None

class GoalCreate(GoalBase):
    employee_id: str
    appraisal_id: Optional[str] = None

class GoalUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    achieved_value: Optional[float] = None
    target_value: Optional[float] = None

class GoalPublic(GoalBase):
    id: str
    employee_id: str
    achievement_percentage: float
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ==================== KPI SCHEMAS ====================

class KPIBase(BaseModel):
    title: str = Field(..., min_length=3, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    status: str = Field(default='Active')  # Active, Paused, Completed
    target_value: float = Field(..., gt=0)
    achieved_value: Optional[float] = Field(default=0.0)
    weightage: float = Field(default=0.0, ge=0, le=100)
    start_date: date
    end_date: date

class KPICreate(KPIBase):
    employee_id: str
    goal_id: Optional[str] = None

class KPIUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    target_value: Optional[float] = None
    achieved_value: Optional[float] = None
    weightage: Optional[float] = None

class KPIPublic(KPIBase):
    id: str
    employee_id: str
    goal_id: Optional[str]
    created_at: datetime
    updated_at: datetime

    @property
    def achievement_percentage(self) -> float:
        if self.achieved_value is None or self.target_value == 0:
            return 0.0
        return min((self.achieved_value / self.target_value) * 100, 100.0)

    class Config:
        from_attributes = True


# ==================== PERFORMANCE APPRAISAL SCHEMAS ====================

class PerformanceAppraisalBase(BaseModel):
    review_period: str = Field(..., min_length=3, max_length=100)
    status: str = Field(default='Draft')  # Draft, Submitted, Completed
    rating: Optional[float] = Field(None, ge=0, le=5)
    goals_achieved: Optional[str] = None
    areas_for_improvement: Optional[str] = None
    comments: Optional[str] = None
    review_date: Optional[date] = None
    next_review_date: Optional[date] = None

class PerformanceAppraisalCreate(PerformanceAppraisalBase):
    employee_id: str
    reviewer_id: Optional[str] = None

class PerformanceAppraisalUpdate(BaseModel):
    status: Optional[str] = None
    rating: Optional[float] = None
    goals_achieved: Optional[str] = None
    areas_for_improvement: Optional[str] = None
    comments: Optional[str] = None
    review_date: Optional[date] = None
    next_review_date: Optional[date] = None

class PerformanceAppraisalPublic(PerformanceAppraisalBase):
    id: str
    employee_id: str
    reviewer_id: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ==================== TRAINING SCHEMAS ====================

class TrainingCourseBase(BaseModel):
    title: str = Field(..., min_length=3, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    instructor: Optional[str] = Field(None, max_length=120)
    duration_hours: Optional[float] = None

class TrainingCourseCreate(TrainingCourseBase):
    pass

class TrainingCourseUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    instructor: Optional[str] = None
    duration_hours: Optional[float] = None

class TrainingCoursePublic(TrainingCourseBase):
    id: str
    created_at: datetime

    class Config:
        from_attributes = True


class EmployeeTrainingBase(BaseModel):
    status: str = Field(default='Enrolled')  # Enrolled, In Progress, Completed
    completion_date: Optional[date] = None

class EmployeeTrainingCreate(EmployeeTrainingBase):
    employee_id: str
    course_id: str

class EmployeeTrainingUpdate(BaseModel):
    status: Optional[str] = None
    completion_date: Optional[date] = None

class EmployeeTrainingPublic(EmployeeTrainingBase):
    id: str
    employee_id: str
    course_id: str
    created_at: datetime

    class Config:
        from_attributes = True


# ==================== CERTIFICATION SCHEMAS ====================

class CertificationBase(BaseModel):
    name: str = Field(..., min_length=3, max_length=200)
    issuing_authority: str = Field(..., min_length=2, max_length=120)
    issue_date: date
    expiry_date: Optional[date] = None

class CertificationCreate(CertificationBase):
    employee_id: str

class CertificationUpdate(BaseModel):
    name: Optional[str] = None
    issuing_authority: Optional[str] = None
    issue_date: Optional[date] = None
    expiry_date: Optional[date] = None

class CertificationPublic(CertificationBase):
    id: str
    employee_id: str
    created_at: datetime
    is_expired: Optional[bool] = False

    class Config:
        from_attributes = True
