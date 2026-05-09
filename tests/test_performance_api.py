import pytest
from sqlalchemy.orm import Session
from datetime import date
from app.db.database import SessionLocal
from app.db.models import Base, engine, User, Employee, PerformanceAppraisal, Goal, KPI
from app.services.performance_service import PerformanceService, GoalService, KPIService
from app.schemas.performance import (
    PerformanceAppraisalCreate, GoalCreate, KPICreate
)


@pytest.fixture
def db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    yield db
    db.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def test_user(db: Session):
    user = User(
        id='user1',
        username='testuser',
        email='test@example.com',
        hashed_password='hashed',
        is_active=True
    )
    db.add(user)
    db.commit()
    return user


@pytest.fixture
def test_employee(db: Session, test_user: User):
    employee = Employee(
        id='emp1',
        user_id='user1',
        full_name='Test Employee',
        email='emp@example.com',
        phone='1234567890',
        date_of_birth=date(1990, 1, 1),
        gender='M'
    )
    db.add(employee)
    db.commit()
    return employee


def test_create_goal(db: Session, test_employee: Employee):
    payload = GoalCreate(
        title='Sales Target',
        description='Increase sales by 20%',
        employee_id=test_employee.id,
        start_date=date(2026, 1, 1),
        end_date=date(2026, 3, 31),
        target_value=100000,
        achieved_value=0,
        status='Active'
    )
    
    goal = GoalService.create_goal(db, payload)
    assert goal.title == 'Sales Target'
    assert goal.employee_id == test_employee.id
    assert goal.status == 'Active'
    assert goal.target_value == 100000


def test_create_kpi(db: Session, test_employee: Employee):
    payload = KPICreate(
        title='Quarterly Revenue',
        description='Q1 Revenue Target',
        employee_id=test_employee.id,
        target_value=50000,
        achieved_value=0,
        weightage=30,
        start_date=date(2026, 1, 1),
        end_date=date(2026, 3, 31),
        status='Active'
    )
    
    kpi = KPIService.create_kpi(db, payload)
    assert kpi.title == 'Quarterly Revenue'
    assert kpi.target_value == 50000
    assert kpi.weightage == 30


def test_get_employee_performance_score(db: Session, test_employee: Employee):
    # Create multiple KPIs
    kpi1 = KPICreate(
        title='KPI 1',
        employee_id=test_employee.id,
        target_value=100,
        achieved_value=80,
        weightage=50,
        start_date=date(2026, 1, 1),
        end_date=date(2026, 3, 31),
        status='Active'
    )
    kpi2 = KPICreate(
        title='KPI 2',
        employee_id=test_employee.id,
        target_value=100,
        achieved_value=90,
        weightage=50,
        start_date=date(2026, 1, 1),
        end_date=date(2026, 3, 31),
        status='Active'
    )
    
    KPIService.create_kpi(db, kpi1)
    KPIService.create_kpi(db, kpi2)
    
    score = KPIService.get_employee_performance_score(db, test_employee.id)
    assert 'score' in score
    assert 'kpi_count' in score
    assert score['kpi_count'] == 2
    # Expected score: (80/100 * 50 + 90/100 * 50) / 100 = (40 + 45) / 100 = 85%
    assert score['score'] == 85.0


def test_update_goal(db: Session, test_employee: Employee):
    payload = GoalCreate(
        title='Sales Target',
        description='Increase sales by 20%',
        employee_id=test_employee.id,
        start_date=date(2026, 1, 1),
        end_date=date(2026, 3, 31),
        target_value=100000,
        achieved_value=0,
        status='Active'
    )
    
    goal = GoalService.create_goal(db, payload)
    
    from app.schemas.performance import GoalUpdate
    update = GoalUpdate(achieved_value=75000)
    updated_goal = GoalService.update_goal(db, goal.id, update)
    
    assert updated_goal.achieved_value == 75000
    assert updated_goal.achievement_percentage == 75.0


def test_create_performance_appraisal(db: Session, test_employee: Employee):
    payload = PerformanceAppraisalCreate(
        employee_id=test_employee.id,
        review_period='Q1 2026',
        status='Draft',
        rating=4.5,
        comments='Good performance'
    )
    
    appraisal = PerformanceService.create_appraisal(db, payload)
    assert appraisal.review_period == 'Q1 2026'
    assert appraisal.rating == 4.5
    assert appraisal.status == 'Draft'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
