from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from sqlalchemy import text

from app.api.routes.auth import router as auth_router
from app.api.routes.org import router as org_router
from app.api.routes.employees import router as employees_router
from app.api.routes.dashboard import router as dashboard_router
from app.api.routes.attendance import router as attendance_router
from app.api.routes.leave import router as leave_router
from app.api.routes.payroll import router as payroll_router
from app.core.config import settings
from app.db.database import engine, SessionLocal
from app.db.models import Base, seed_demo_users, seed_demo_org, seed_demo_shifts, seed_demo_leave_data, seed_demo_salary_data

app = FastAPI(title=settings.app_name)

uploads_dir = Path(__file__).resolve().parents[1] / 'uploads'
uploads_dir.mkdir(parents=True, exist_ok=True)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

app.include_router(auth_router, prefix='/auth', tags=['auth'])
app.include_router(org_router, prefix='/org', tags=['org'])
app.include_router(employees_router, prefix='/employees', tags=['employees'])
app.include_router(dashboard_router, prefix='/dashboard', tags=['dashboard'])
app.include_router(attendance_router, prefix='/attendance', tags=['attendance'])
app.include_router(leave_router, prefix='/leave', tags=['leave'])
app.include_router(payroll_router, prefix='/payroll', tags=['payroll'])
from app.api.routes.admin import router as admin_router
from app.api.routes.advanced_attendance import router as adv_attendance_router
from app.api.routes.engagement import router as engagement_router
from app.api.routes.todo import router as todo_router
from app.api.routes.lifecycle import router as lifecycle_router

from app.api.routes.recruitment import router as recruitment_router
from app.api.routes.documents import router as documents_router
from app.api.routes.financials import router as financials_router

app.include_router(admin_router, prefix='/admin', tags=['admin'])
app.include_router(adv_attendance_router, prefix='/advanced-attendance', tags=['advanced_attendance'])
app.include_router(engagement_router, prefix='/engagement', tags=['engagement'])
app.include_router(recruitment_router, prefix='/recruitment', tags=['recruitment'])
app.include_router(documents_router, prefix='/documents', tags=['documents'])
app.include_router(financials_router, prefix='/financials', tags=['financials'])
app.include_router(todo_router, prefix='/todo', tags=['todo'])
app.include_router(lifecycle_router, prefix='/lifecycle', tags=['lifecycle'])
app.mount('/uploads', StaticFiles(directory=uploads_dir), name='uploads')


@app.on_event('startup')
def startup() -> None:
    Base.metadata.create_all(bind=engine)
    _ensure_attendance_columns()
    # Run each seeder in its own session. If one seeder fails, rollback and continue
    seeders = [
        seed_demo_users,
        seed_demo_org,
        seed_demo_shifts,
        seed_demo_leave_data,
        seed_demo_salary_data,
    ]
    for seeder in seeders:
        with SessionLocal() as session:
            try:
                seeder(session)
            except Exception:
                # ensure session is clean for next seeder
                try:
                    session.rollback()
                except Exception:
                    pass


def _ensure_attendance_columns() -> None:
    """Backfill older databases that were created before attendance geo columns existed."""
    required_columns = {
        'check_in_latitude': 'NUMERIC(10, 8)',
        'check_in_longitude': 'NUMERIC(11, 8)',
        'check_out_latitude': 'NUMERIC(10, 8)',
        'check_out_longitude': 'NUMERIC(11, 8)',
        'location_verified': 'BOOLEAN NOT NULL DEFAULT FALSE',
    }

    with engine.begin() as conn:
        existing = {
            row[0]
            for row in conn.execute(
                text(
                    """
                    SELECT column_name
                    FROM information_schema.columns
                    WHERE table_name = 'attendance'
                    """
                )
            )
        }

        for column_name, sql_type in required_columns.items():
            if column_name in existing:
                continue
            conn.execute(text(f"ALTER TABLE attendance ADD COLUMN {column_name} {sql_type}"))


@app.get('/')
def root() -> dict[str, str]:
    return {'message': 'HRMS API is running'}


@app.get('/health')
def health() -> dict[str, str]:
    return {'status': 'ok'}
