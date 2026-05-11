from sqlalchemy.orm import Session
from sqlalchemy import and_, desc
from app.db.models import EmployeeGrievance
from app.schemas.grievance import (
    EmployeeGrievanceCreate,
    EmployeeGrievanceStatusUpdate,
    GrievanceInvestigationUpdate,
)
from typing import List, Tuple
from datetime import datetime


def create_grievance(
    grievance: EmployeeGrievanceCreate,
    employee_id: str,
    db: Session,
) -> EmployeeGrievance:
    """Create a new employee grievance"""
    db_grievance = EmployeeGrievance(
        employee_id=employee_id,
        against_employee_id=grievance.against_employee_id,
        subject=grievance.subject,
        description=grievance.description,
        status="Submitted",
        created_at=datetime.utcnow(),
    )
    db.add(db_grievance)
    db.commit()
    db.refresh(db_grievance)
    return db_grievance


def get_grievances(
    db: Session,
    employee_id: str = None,
    status_filter: str = None,
    page: int = 1,
    size: int = 20,
) -> Tuple[List[EmployeeGrievance], int]:
    """Get grievances with pagination and filtering"""
    query = db.query(EmployeeGrievance)
    
    # Employee filter - only see own grievances unless they're HR/Admin
    if employee_id:
        query = query.filter(EmployeeGrievance.employee_id == employee_id)
    
    # Status filter
    if status_filter:
        query = query.filter(EmployeeGrievance.status == status_filter)
    
    total = query.count()
    grievances = (
        query.order_by(desc(EmployeeGrievance.created_at))
        .offset((page - 1) * size)
        .limit(size)
        .all()
    )
    
    return grievances, total


def get_all_grievances(
    db: Session,
    status_filter: str = None,
    page: int = 1,
    size: int = 20,
) -> Tuple[List[EmployeeGrievance], int]:
    """Get all grievances (admin view) with pagination and filtering"""
    query = db.query(EmployeeGrievance)
    
    # Status filter
    if status_filter:
        query = query.filter(EmployeeGrievance.status == status_filter)
    
    total = query.count()
    grievances = (
        query.order_by(desc(EmployeeGrievance.created_at))
        .offset((page - 1) * size)
        .limit(size)
        .all()
    )
    
    return grievances, total


def get_grievance(db: Session, grievance_id: str) -> EmployeeGrievance:
    """Get a specific grievance by ID"""
    return db.query(EmployeeGrievance).filter(
        EmployeeGrievance.id == grievance_id
    ).first()


def update_grievance_status(
    grievance_id: str,
    status_update: EmployeeGrievanceStatusUpdate,
    db: Session,
) -> EmployeeGrievance:
    """Update grievance status"""
    grievance = get_grievance(db, grievance_id)
    if not grievance:
        return None
    
    grievance.status = status_update.status
    grievance.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(grievance)
    return grievance

def investigate_grievance(
    grievance_id: str,
    investigation_update: GrievanceInvestigationUpdate,
    db: Session,
) -> EmployeeGrievance:
    """Update grievance investigation details"""
    grievance = get_grievance(db, grievance_id)
    if not grievance:
        return None
    
    if investigation_update.investigator_id is not None:
        grievance.investigator_id = investigation_update.investigator_id
    if investigation_update.investigation_notes is not None:
        grievance.investigation_notes = investigation_update.investigation_notes
    if investigation_update.meeting_scheduled_at is not None:
        grievance.meeting_scheduled_at = investigation_update.meeting_scheduled_at
    if investigation_update.status is not None:
        grievance.status = investigation_update.status

    grievance.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(grievance)
    return grievance

