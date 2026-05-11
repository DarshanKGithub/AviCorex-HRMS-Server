from sqlalchemy.orm import Session
from sqlalchemy import desc, and_
from datetime import datetime, date, timezone
from uuid import uuid4
from app.db.models import (
    PerformanceAppraisal, Goal, KPI, Employee,
    TrainingCourse, EmployeeTraining, Certification
)
from app.schemas.performance import (
    PerformanceAppraisalCreate, PerformanceAppraisalUpdate,
    GoalCreate, GoalUpdate,
    KPICreate, KPIUpdate,
    EmployeeTrainingCreate, EmployeeTrainingUpdate,
    CertificationCreate, CertificationUpdate,
    TrainingCourseCreate, TrainingCourseUpdate
)


class PerformanceService:
    """Service for performance appraisal management"""

    @staticmethod
    def create_appraisal(db: Session, payload: PerformanceAppraisalCreate) -> PerformanceAppraisal:
        appraisal = PerformanceAppraisal(
            id=str(uuid4()),
            employee_id=payload.employee_id,
            reviewer_id=payload.reviewer_id,
            review_period=payload.review_period,
            status=payload.status,
            rating=payload.rating,
            goals_achieved=payload.goals_achieved,
            areas_for_improvement=payload.areas_for_improvement,
            comments=payload.comments,
            review_date=payload.review_date,
            next_review_date=payload.next_review_date,
        )
        db.add(appraisal)
        db.commit()
        db.refresh(appraisal)
        return appraisal

    @staticmethod
    def get_appraisal(db: Session, appraisal_id: str) -> PerformanceAppraisal:
        return db.query(PerformanceAppraisal).filter(PerformanceAppraisal.id == appraisal_id).first()

    @staticmethod
    def get_appraisals_for_employee(db: Session, employee_id: str) -> list[PerformanceAppraisal]:
        return db.query(PerformanceAppraisal).filter(
            PerformanceAppraisal.employee_id == employee_id
        ).order_by(desc(PerformanceAppraisal.created_at)).all()

    @staticmethod
    def get_appraisals_by_reviewer(db: Session, reviewer_id: str) -> list[PerformanceAppraisal]:
        return db.query(PerformanceAppraisal).filter(
            PerformanceAppraisal.reviewer_id == reviewer_id
        ).order_by(desc(PerformanceAppraisal.created_at)).all()

    @staticmethod
    def update_appraisal(db: Session, appraisal_id: str, payload: PerformanceAppraisalUpdate) -> PerformanceAppraisal:
        appraisal = db.query(PerformanceAppraisal).filter(PerformanceAppraisal.id == appraisal_id).first()
        if not appraisal:
            return None
        
        update_data = payload.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(appraisal, field, value)
        
        appraisal.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(appraisal)
        return appraisal

    @staticmethod
    def delete_appraisal(db: Session, appraisal_id: str) -> bool:
        appraisal = db.query(PerformanceAppraisal).filter(PerformanceAppraisal.id == appraisal_id).first()
        if appraisal:
            db.delete(appraisal)
            db.commit()
            return True
        return False


class GoalService:
    """Service for goal/objective management"""

    @staticmethod
    def create_goal(db: Session, payload: GoalCreate) -> Goal:
        achievement_percentage = 0.0
        if payload.target_value and payload.target_value > 0 and payload.achieved_value:
            achievement_percentage = min((float(payload.achieved_value) / float(payload.target_value)) * 100, 100.0)
        
        goal = Goal(
            id=str(uuid4()),
            employee_id=payload.employee_id,
            appraisal_id=payload.appraisal_id,
            title=payload.title,
            description=payload.description,
            status=payload.status,
            start_date=payload.start_date,
            end_date=payload.end_date,
            target_value=payload.target_value,
            achieved_value=payload.achieved_value,
            achievement_percentage=achievement_percentage,
        )
        db.add(goal)
        db.commit()
        db.refresh(goal)
        return goal

    @staticmethod
    def get_goal(db: Session, goal_id: str) -> Goal:
        return db.query(Goal).filter(Goal.id == goal_id).first()

    @staticmethod
    def get_goals_for_employee(db: Session, employee_id: str, status: str = None) -> list[Goal]:
        query = db.query(Goal).filter(Goal.employee_id == employee_id)
        if status:
            query = query.filter(Goal.status == status)
        return query.order_by(desc(Goal.created_at)).all()

    @staticmethod
    def get_goals_for_appraisal(db: Session, appraisal_id: str) -> list[Goal]:
        return db.query(Goal).filter(Goal.appraisal_id == appraisal_id).order_by(desc(Goal.created_at)).all()

    @staticmethod
    def update_goal(db: Session, goal_id: str, payload: GoalUpdate) -> Goal:
        goal = db.query(Goal).filter(Goal.id == goal_id).first()
        if not goal:
            return None
        
        update_data = payload.model_dump(exclude_unset=True)
        
        # Recalculate achievement percentage if values updated
        if 'achieved_value' in update_data or 'target_value' in update_data:
            target = update_data.get('target_value', goal.target_value)
            achieved = update_data.get('achieved_value', goal.achieved_value)
            if target and target > 0 and achieved:
                goal.achievement_percentage = min((float(achieved) / float(target)) * 100, 100.0)
        
        for field, value in update_data.items():
            if field != 'achievement_percentage':
                setattr(goal, field, value)
        
        goal.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(goal)
        return goal

    @staticmethod
    def delete_goal(db: Session, goal_id: str) -> bool:
        goal = db.query(Goal).filter(Goal.id == goal_id).first()
        if goal:
            db.delete(goal)
            db.commit()
            return True
        return False


class KPIService:
    """Service for KPI management"""

    @staticmethod
    def create_kpi(db: Session, payload: KPICreate) -> KPI:
        achievement_percentage = 0.0
        if payload.target_value and payload.target_value > 0 and payload.achieved_value:
            achievement_percentage = min((float(payload.achieved_value) / float(payload.target_value)) * 100, 100.0)
        
        kpi = KPI(
            id=str(uuid4()),
            employee_id=payload.employee_id,
            goal_id=payload.goal_id,
            title=payload.title,
            description=payload.description,
            status=payload.status,
            target_value=payload.target_value,
            achieved_value=payload.achieved_value or 0.0,
            weightage=payload.weightage,
            start_date=payload.start_date,
            end_date=payload.end_date,
        )
        db.add(kpi)
        db.commit()
        db.refresh(kpi)
        return kpi

    @staticmethod
    def get_kpi(db: Session, kpi_id: str) -> KPI:
        return db.query(KPI).filter(KPI.id == kpi_id).first()

    @staticmethod
    def get_kpis_for_employee(db: Session, employee_id: str, status: str = None) -> list[KPI]:
        query = db.query(KPI).filter(KPI.employee_id == employee_id)
        if status:
            query = query.filter(KPI.status == status)
        return query.order_by(desc(KPI.created_at)).all()

    @staticmethod
    def get_kpis_for_goal(db: Session, goal_id: str) -> list[KPI]:
        return db.query(KPI).filter(KPI.goal_id == goal_id).order_by(desc(KPI.created_at)).all()

    @staticmethod
    def update_kpi(db: Session, kpi_id: str, payload: KPIUpdate) -> KPI:
        kpi = db.query(KPI).filter(KPI.id == kpi_id).first()
        if not kpi:
            return None
        
        update_data = payload.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(kpi, field, value)
        
        kpi.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(kpi)
        return kpi

    @staticmethod
    def delete_kpi(db: Session, kpi_id: str) -> bool:
        kpi = db.query(KPI).filter(KPI.id == kpi_id).first()
        if kpi:
            db.delete(kpi)
            db.commit()
            return True
        return False

    @staticmethod
    def get_employee_performance_score(db: Session, employee_id: str) -> dict:
        """Calculate weighted performance score for an employee"""
        kpis = KPIService.get_kpis_for_employee(db, employee_id, status='Active')
        
        if not kpis:
            return {'score': 0.0, 'total_weight': 0, 'kpi_count': 0}
        
        total_weight = sum(kpi.weightage for kpi in kpis)
        if total_weight == 0:
            return {'score': 0.0, 'total_weight': 0, 'kpi_count': len(kpis)}
        
        weighted_score = 0.0
        for kpi in kpis:
            target_value = float(kpi.target_value or 0)
            achieved_value = float(kpi.achieved_value or 0)
            weightage = float(kpi.weightage or 0)
            achievement = min((achieved_value / target_value) * 100, 100) if target_value > 0 else 0
            weighted_score += (achievement * weightage) / 100
        
        return {
            'score': round(weighted_score / float(total_weight) * 100, 2),
            'total_weight': float(total_weight),
            'kpi_count': len(kpis)
        }


class TrainingService:
    """Service for training and certification management"""

    @staticmethod
    def create_course(db: Session, payload: TrainingCourseCreate) -> TrainingCourse:
        course = TrainingCourse(
            id=str(uuid4()),
            title=payload.title,
            description=payload.description,
            instructor=payload.instructor,
            duration_hours=payload.duration_hours,
        )
        db.add(course)
        db.commit()
        db.refresh(course)
        return course

    @staticmethod
    def get_course(db: Session, course_id: str) -> TrainingCourse:
        return db.query(TrainingCourse).filter(TrainingCourse.id == course_id).first()

    @staticmethod
    def get_all_courses(db: Session) -> list[TrainingCourse]:
        return db.query(TrainingCourse).order_by(desc(TrainingCourse.created_at)).all()

    @staticmethod
    def update_course(db: Session, course_id: str, payload: TrainingCourseUpdate) -> TrainingCourse:
        course = db.query(TrainingCourse).filter(TrainingCourse.id == course_id).first()
        if not course:
            return None
        
        update_data = payload.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(course, field, value)
        
        db.commit()
        db.refresh(course)
        return course

    @staticmethod
    def delete_course(db: Session, course_id: str) -> bool:
        course = db.query(TrainingCourse).filter(TrainingCourse.id == course_id).first()
        if course:
            db.delete(course)
            db.commit()
            return True
        return False

    @staticmethod
    def enroll_employee(db: Session, payload: EmployeeTrainingCreate) -> EmployeeTraining:
        training = EmployeeTraining(
            id=str(uuid4()),
            employee_id=payload.employee_id,
            course_id=payload.course_id,
            status=payload.status,
            completion_date=payload.completion_date,
        )
        db.add(training)
        db.commit()
        db.refresh(training)
        return training

    @staticmethod
    def get_employee_training(db: Session, training_id: str) -> EmployeeTraining:
        return db.query(EmployeeTraining).filter(EmployeeTraining.id == training_id).first()

    @staticmethod
    def get_trainings_for_employee(db: Session, employee_id: str) -> list[EmployeeTraining]:
        return db.query(EmployeeTraining).filter(
            EmployeeTraining.employee_id == employee_id
        ).order_by(desc(EmployeeTraining.created_at)).all()

    @staticmethod
    def update_training(db: Session, training_id: str, payload: EmployeeTrainingUpdate) -> EmployeeTraining:
        training = db.query(EmployeeTraining).filter(EmployeeTraining.id == training_id).first()
        if not training:
            return None
        
        update_data = payload.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(training, field, value)
        
        db.commit()
        db.refresh(training)
        return training

    @staticmethod
    def delete_training(db: Session, training_id: str) -> bool:
        training = db.query(EmployeeTraining).filter(EmployeeTraining.id == training_id).first()
        if training:
            db.delete(training)
            db.commit()
            return True
        return False


class CertificationService:
    """Service for certification management"""

    @staticmethod
    def create_certification(db: Session, payload: CertificationCreate) -> Certification:
        cert = Certification(
            id=str(uuid4()),
            employee_id=payload.employee_id,
            name=payload.name,
            issuing_authority=payload.issuing_authority,
            issue_date=payload.issue_date,
            expiry_date=payload.expiry_date,
        )
        db.add(cert)
        db.commit()
        db.refresh(cert)
        return cert

    @staticmethod
    def get_certification(db: Session, cert_id: str) -> Certification:
        return db.query(Certification).filter(Certification.id == cert_id).first()

    @staticmethod
    def get_certifications_for_employee(db: Session, employee_id: str) -> list[Certification]:
        return db.query(Certification).filter(
            Certification.employee_id == employee_id
        ).order_by(desc(Certification.created_at)).all()

    @staticmethod
    def update_certification(db: Session, cert_id: str, payload: CertificationUpdate) -> Certification:
        cert = db.query(Certification).filter(Certification.id == cert_id).first()
        if not cert:
            return None
        
        update_data = payload.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(cert, field, value)
        
        db.commit()
        db.refresh(cert)
        return cert

    @staticmethod
    def delete_certification(db: Session, cert_id: str) -> bool:
        cert = db.query(Certification).filter(Certification.id == cert_id).first()
        if cert:
            db.delete(cert)
            db.commit()
            return True
        return False

    @staticmethod
    def get_expired_certifications(db: Session, employee_id: str = None) -> list[Certification]:
        query = db.query(Certification).filter(
            and_(
                Certification.expiry_date.isnot(None),
                Certification.expiry_date < date.today()
            )
        )
        if employee_id:
            query = query.filter(Certification.employee_id == employee_id)
        return query.all()
