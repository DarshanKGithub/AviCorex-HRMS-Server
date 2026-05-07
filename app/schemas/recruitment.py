from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class JobPostingCreate(BaseModel):
    title: str
    department_id: Optional[str] = None
    location: Optional[str] = None
    employment_type: Optional[str] = None
    description: str
    requirements: Optional[str] = None
    status: Optional[str] = 'Open'

class JobPostingPublic(JobPostingCreate):
    id: str
    created_at: datetime

class CandidateCreate(BaseModel):
    first_name: str
    last_name: str
    email: str
    phone: Optional[str] = None
    resume_url: Optional[str] = None
    parsed_skills: Optional[str] = None
    source: Optional[str] = None

class CandidatePublic(CandidateCreate):
    id: str
    created_at: datetime

class JobApplicationCreate(BaseModel):
    job_id: str
    candidate_id: str
    status: Optional[str] = 'Applied'

class JobApplicationPublic(JobApplicationCreate):
    id: str
    applied_at: datetime

class InterviewCreate(BaseModel):
    application_id: str
    interviewer_id: str
    scheduled_at: datetime
    meeting_link: Optional[str] = None

class InterviewPublic(InterviewCreate):
    id: str
    status: str
    feedback: Optional[str] = None
    rating: Optional[int] = None
    created_at: datetime

class PaginatedJobPostings(BaseModel):
    items: List[JobPostingPublic]
    total: int
    page: int
    size: int
