from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.database import Base
from app.db.models import Department, Employee
from app.services.dashboard_service import get_dashboard_summary


def make_session():
    engine = create_engine('sqlite:///:memory:', future=True)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
    return Session()


def test_dashboard_summary_counts_and_breakdown():
    session = make_session()
    try:
        engineering = Department(name='Engineering')
        people = Department(name='People Ops')
        session.add_all([engineering, people])
        session.commit()
        session.refresh(engineering)
        session.refresh(people)

        session.add_all(
            [
                Employee(full_name='Alice', email='alice@example.com', department_id=engineering.id, is_active=True),
                Employee(full_name='Bob', email='bob@example.com', department_id=engineering.id, is_active=False),
                Employee(full_name='Cara', email='cara@example.com', department_id=people.id, is_active=True),
                Employee(full_name='Dan', email='dan@example.com', is_active=True),
            ]
        )
        session.commit()

        summary = get_dashboard_summary(db=session)

        assert summary.kpis.total_employees == 4
        assert summary.kpis.active_employees == 3
        assert summary.kpis.inactive_employees == 1
        assert summary.kpis.departments_count == 2
        assert summary.kpis.pending_approvals == 0

        by_name = {item.department_name: item for item in summary.department_breakdown}
        assert by_name['Engineering'].total_employees == 2
        assert by_name['Engineering'].active_employees == 1
        assert by_name['Engineering'].inactive_employees == 1
        assert by_name['People Ops'].total_employees == 1
        assert by_name['Unassigned'].total_employees == 1
    finally:
        session.close()


def test_dashboard_summary_department_filter():
    session = make_session()
    try:
        engineering = Department(name='Engineering')
        people = Department(name='People Ops')
        session.add_all([engineering, people])
        session.commit()
        session.refresh(engineering)

        session.add_all(
            [
                Employee(full_name='Alice', email='alice@example.com', department_id=engineering.id, is_active=True),
                Employee(full_name='Bob', email='bob@example.com', department_id=engineering.id, is_active=False),
                Employee(full_name='Cara', email='cara@example.com', department_id=people.id, is_active=True),
            ]
        )
        session.commit()

        summary = get_dashboard_summary(db=session, department_id=engineering.id)

        assert summary.kpis.total_employees == 2
        assert summary.kpis.active_employees == 1
        assert summary.kpis.inactive_employees == 1
        assert summary.kpis.departments_count == 1
        assert len(summary.department_breakdown) == 1
        assert summary.department_breakdown[0].department_name == 'Engineering'
    finally:
        session.close()
