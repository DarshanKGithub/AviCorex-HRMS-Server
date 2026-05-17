import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from app.db.database import Base
from app.db.models import User, LeaveBalance, LeaveType
from app.services.employee_service import create_employee_with_account
from app.schemas.employee import EmployeeCreateWithAccount


@pytest.fixture()
def db_session():
    engine = create_engine('sqlite:///:memory:', future=True)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
    session = Session()
    session.add(LeaveType(name='Casual Leave', description='Test', default_days_per_year=7, is_active=True))
    session.commit()
    try:
        yield session
    finally:
        session.close()


def test_create_employee_with_account_links_user_and_provisions_leave(db_session):
    payload = EmployeeCreateWithAccount(
        full_name='Test Hire',
        email='new.hire@hrms.com',
        password='Secret123',
        role='Employee',
    )
    emp = create_employee_with_account(payload, db_session, actor_id=None)

    user = db_session.scalar(select(User).where(User.email == 'new.hire@hrms.com'))
    assert user is not None
    assert user.id == emp.id
    assert user.role == 'Employee'

    balances = db_session.scalars(select(LeaveBalance).where(LeaveBalance.employee_id == emp.id)).all()
    assert len(balances) > 0
