from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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
app.include_router(admin_router, prefix='/admin', tags=['admin'])


@app.on_event('startup')
def startup() -> None:
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as session:
        seed_demo_users(session)
        # seed Phase 2 default org data
        seed_demo_org(session)
        # seed Phase 4 default shift and rule data
        seed_demo_shifts(session)
        # seed Phase 5 leave types and holidays
        seed_demo_leave_data(session)
        # seed Phase 6 salary components
        seed_demo_salary_data(session)


@app.get('/')
def root() -> dict[str, str]:
    return {'message': 'HRMS API is running'}


@app.get('/health')
def health() -> dict[str, str]:
    return {'status': 'ok'}
