import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timezone

from app.db.database import Base
from app.schemas.recruitment import (
    CandidateCreate,
    InterviewCreate,
    InterviewStatusUpdate,
    JobApplicationCreate,
    JobApplicationStatusUpdate,
    JobPostingCreate,
    JobPostingUpdate,
)
from app.services.recruitment_service import (
    create_candidate,
    create_job_application,
    create_job_posting,
    parse_resume_text,
    update_application_status,
    update_job_posting,
    update_interview_status,
    schedule_interview,
)
from app.db.models import Candidate, JobApplication, JobPosting


@pytest.fixture()
def db_session():
    engine = create_engine('sqlite:///:memory:', future=True)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
    session = Session()
    try:
        yield session
    finally:
        session.close()


def test_parse_resume_extracts_skills():
    result = parse_resume_text('Python developer with React, FastAPI, Docker and AWS experience')

    assert set(result.parsed_skills) == {'python', 'react', 'fastapi', 'docker', 'aws'}
    assert 'python' in result.summary.lower()


def test_candidate_creation_parses_resume_text(db_session):
    candidate = create_candidate(
        CandidateCreate(
            first_name='Asha',
            last_name='Patel',
            email='asha@example.com',
            resume_text='Built APIs in Python and FastAPI with PostgreSQL and AWS.',
            source='Website',
        ),
        db_session,
    )

    assert candidate.email == 'asha@example.com'
    assert candidate.parsed_skills is not None
    assert 'python' in candidate.parsed_skills.lower()
    assert 'fastapi' in candidate.parsed_skills.lower()


def test_application_and_status_lifecycle(db_session):
    job = create_job_posting(
        JobPostingCreate(
            title='Backend Engineer',
            description='Build APIs',
            location='Remote',
            employment_type='Full-time',
            status='Open',
        ),
        db_session,
    )
    candidate = create_candidate(
        CandidateCreate(
            first_name='Dev',
            last_name='Kumar',
            email='dev@example.com',
            source='Referral',
        ),
        db_session,
    )

    application = create_job_application(
        JobApplicationCreate(job_id=job.id, candidate_id=candidate.id, status='Applied'),
        db_session,
    )
    assert application.status == 'Applied'

    updated_application = update_application_status(
        application.id,
        JobApplicationStatusUpdate(status='Interviewing'),
        db_session,
    )
    assert updated_application.status == 'Interviewing'


def test_job_update_and_interview_lifecycle(db_session):
    job = create_job_posting(
        JobPostingCreate(title='QA Engineer', description='Test the product', status='Draft'),
        db_session,
    )
    updated_job = update_job_posting(job.id, JobPostingUpdate(status='Open', location='Bengaluru'), db_session)
    assert updated_job.status == 'Open'
    assert updated_job.location == 'Bengaluru'

    candidate = create_candidate(
        CandidateCreate(first_name='Nina', last_name='Shah', email='nina@example.com'),
        db_session,
    )
    application = create_job_application(
        JobApplicationCreate(job_id=job.id, candidate_id=candidate.id),
        db_session,
    )

    interview = schedule_interview(
        InterviewCreate(
            application_id=application.id,
            interviewer_id='interviewer-1',
            scheduled_at=datetime(2026, 5, 9, 10, 30, tzinfo=timezone.utc),
            meeting_link='https://meet.example.com/interview',
        ),
        db_session,
    )
    assert interview.status == 'Scheduled'
    assert interview.meeting_link == 'https://meet.example.com/interview'

    updated_interview = update_interview_status(
        interview.id,
        InterviewStatusUpdate(status='Completed', feedback='Strong candidate', rating=5),
        db_session,
    )
    assert updated_interview.status == 'Completed'
    assert updated_interview.feedback == 'Strong candidate'
    assert updated_interview.rating == 5
