from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from app.api.routes.auth import router as auth_router
from app.api.routes.org import router as org_router
from app.api.routes.employees import router as employees_router
from app.api.routes.dashboard import router as dashboard_router
from app.api.routes.attendance import router as attendance_router
from app.api.routes.advanced_attendance import router as advanced_attendance_router
from app.api.routes.leave import router as leave_router
from app.api.routes.payroll import router as payroll_router
from app.api.routes.engagement import router as engagement_router
from app.api.routes.performance import router as performance_router
from app.api.routes.todo import router as todo_router
from app.api.routes.recruitment import router as recruitment_router
from app.api.routes.financials import router as financials_router
from app.api.routes.notifications import router as notifications_router
from app.api.routes.workflow import router as workflow_router
from app.api.routes.documents import router as documents_router
from app.api.routes.lifecycle import router as lifecycle_router
from app.core.config import settings
from app.db.database import engine, SessionLocal
from app.db.models import Base, seed_demo_users, seed_demo_org, seed_demo_plans, seed_demo_tenant_subscription, seed_demo_shifts, seed_demo_leave_data, seed_demo_salary_data
import logging


logger = logging.getLogger(__name__)

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
app.include_router(advanced_attendance_router, prefix='/advanced-attendance', tags=['advanced-attendance'])
app.include_router(leave_router, prefix='/leave', tags=['leave'])
app.include_router(payroll_router, prefix='/payroll', tags=['payroll'])
app.include_router(engagement_router, prefix='/engagement', tags=['engagement'])
app.include_router(performance_router)
app.include_router(todo_router, prefix='/todo', tags=['todo'])
app.include_router(recruitment_router, prefix='/recruitment', tags=['recruitment'])
app.include_router(financials_router, prefix='/financials', tags=['financials'])
app.include_router(notifications_router, prefix='/notifications', tags=['notifications'])
app.include_router(workflow_router, prefix='/workflow', tags=['workflow'])
app.include_router(documents_router, prefix='/documents', tags=['documents'])
app.include_router(lifecycle_router, prefix='/lifecycle', tags=['lifecycle'])
from app.api.routes.admin import router as admin_router
from app.api.routes.billing import router as billing_router
app.include_router(admin_router, prefix='/admin', tags=['admin'])
app.include_router(billing_router, prefix='/billing', tags=['billing'])
app.mount('/uploads', StaticFiles(directory=uploads_dir), name='uploads')


@app.on_event('startup')
def startup() -> None:
    Base.metadata.create_all(bind=engine)

    # Run a lightweight schema backfill on startup so missing nullable columns
    # added by earlier deployments do not crash ORM reads before migrations land.
    # Set AUTO_APPLY_SCHEMA_CHANGES=false only if you want to disable this repair step.
    from os import getenv
    if getenv('AUTO_APPLY_SCHEMA_CHANGES', 'true').lower() in ('1', 'true', 'yes'):
        try:
            from app.fix_db import backfill_columns
        except Exception:
            # fallback to top-level fix_db script
            try:
                from fix_db import backfill_columns
            except Exception:
                backfill_columns = None

        if backfill_columns:
            try:
                backfill_columns()
            except Exception:
                logger.exception('Automatic schema backfill failed; continuing startup')

    def run_seed_step(session, step_name: str, step_fn) -> None:
        try:
            step_fn(session)
        except Exception as exc:
            try:
                session.rollback()
            except Exception:
                pass
            logger.exception('Seed step failed: %s (%s)', step_name, exc)

    with SessionLocal() as session:
        run_seed_step(session, 'seed_demo_users', seed_demo_users)
        # seed Phase 2 default org data
        run_seed_step(session, 'seed_demo_org', seed_demo_org)
        # seed subscription plans and demo tenant subscription
        run_seed_step(session, 'seed_demo_plans', seed_demo_plans)
        run_seed_step(session, 'seed_demo_tenant_subscription', seed_demo_tenant_subscription)
        # seed Phase 4 default shift and rule data
        run_seed_step(session, 'seed_demo_shifts', seed_demo_shifts)
        # seed Phase 5 leave types and holidays
        run_seed_step(session, 'seed_demo_leave_data', seed_demo_leave_data)
        # seed Phase 6 salary components
        run_seed_step(session, 'seed_demo_salary_data', seed_demo_salary_data)


@app.get('/')
def root() -> dict[str, str]:
    return {'message': 'HRMS API is running'}


@app.get('/health')
def health() -> dict[str, str]:
    return {'status': 'ok'}
