from pydantic import BaseModel, Field
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
    resume_text: Optional[str] = None
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


class JobPostingUpdate(BaseModel):
    title: Optional[str] = None
    department_id: Optional[str] = None
    location: Optional[str] = None
    employment_type: Optional[str] = None
    description: Optional[str] = None
    requirements: Optional[str] = None
    status: Optional[str] = None


class JobApplicationStatusUpdate(BaseModel):
    status: str = Field(min_length=2)


class InterviewStatusUpdate(BaseModel):
    status: str = Field(min_length=2)
    feedback: Optional[str] = None
    rating: Optional[int] = Field(default=None, ge=1, le=5)


class ResumeParseRequest(BaseModel):
    resume_text: str = Field(min_length=20)


class ResumeParseResponse(BaseModel):
    parsed_skills: List[str]
    summary: str

class PaginatedJobPostings(BaseModel):
    items: List[JobPostingPublic]
    total: int
    page: int
    size: int
