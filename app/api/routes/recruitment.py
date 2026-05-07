from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.core.rbac import get_current_user, require_permissions
from app.db.database import get_db
from app.db.models import User, JobPosting, Candidate, JobApplication, Interview
from app.schemas.recruitment import (
    JobPostingCreate, JobPostingPublic, PaginatedJobPostings,
    CandidateCreate, CandidatePublic,
    JobApplicationCreate, JobApplicationPublic,
    InterviewCreate, InterviewPublic
)

router = APIRouter()

# --- Job Postings ---

@router.post('/jobs', response_model=JobPostingPublic)
def create_job_posting(
    payload: JobPostingCreate,
    user: User = Depends(require_permissions('manage_recruitment')),
    db: Session = Depends(get_db)
):
    job = JobPosting(**payload.model_dump())
    db.add(job)
    db.commit()
    db.refresh(job)
    return JobPostingPublic.model_validate(job, from_attributes=True)

@router.get('/jobs', response_model=PaginatedJobPostings)
def list_jobs(
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    user: User = Depends(get_current_user), # Any logged-in user can see jobs
    db: Session = Depends(get_db)
):
    query = db.query(JobPosting)
    if status:
        query = query.filter(JobPosting.status == status)
    
    total = query.count()
    items = query.order_by(JobPosting.created_at.desc()).offset((page - 1) * size).limit(size).all()
    
    return PaginatedJobPostings(
        items=[JobPostingPublic.model_validate(i, from_attributes=True) for i in items],
        total=total,
        page=page,
        size=size
    )

# --- Candidates ---

@router.post('/candidates', response_model=CandidatePublic)
def add_candidate(
    payload: CandidateCreate,
    user: User = Depends(require_permissions('manage_recruitment')),
    db: Session = Depends(get_db)
):
    candidate = Candidate(**payload.model_dump())
    db.add(candidate)
    db.commit()
    db.refresh(candidate)
    return CandidatePublic.model_validate(candidate, from_attributes=True)

@router.get('/candidates', response_model=list[CandidatePublic])
def list_candidates(
    user: User = Depends(require_permissions('manage_recruitment')),
    db: Session = Depends(get_db)
):
    items = db.query(Candidate).order_by(Candidate.created_at.desc()).all()
    return [CandidatePublic.model_validate(i, from_attributes=True) for i in items]

# --- Applications ---

@router.post('/applications', response_model=JobApplicationPublic)
def apply_job(
    payload: JobApplicationCreate,
    user: User = Depends(require_permissions('manage_recruitment')),
    db: Session = Depends(get_db)
):
    app = JobApplication(**payload.model_dump())
    db.add(app)
    db.commit()
    db.refresh(app)
    return JobApplicationPublic.model_validate(app, from_attributes=True)

@router.get('/applications', response_model=list[JobApplicationPublic])
def list_applications(
    job_id: Optional[str] = Query(None),
    user: User = Depends(require_permissions('manage_recruitment')),
    db: Session = Depends(get_db)
):
    query = db.query(JobApplication)
    if job_id:
        query = query.filter(JobApplication.job_id == job_id)
    items = query.order_by(JobApplication.applied_at.desc()).all()
    return [JobApplicationPublic.model_validate(i, from_attributes=True) for i in items]

# --- Interviews ---

@router.post('/interviews', response_model=InterviewPublic)
def schedule_interview(
    payload: InterviewCreate,
    user: User = Depends(require_permissions('manage_recruitment')),
    db: Session = Depends(get_db)
):
    interview = Interview(**payload.model_dump())
    db.add(interview)
    db.commit()
    db.refresh(interview)
    return InterviewPublic.model_validate(interview, from_attributes=True)
