# HRMS Backend

FastAPI authentication backend for Phase 1 with database-backed authentication.

## Endpoints
- `POST /auth/login`
- `GET /auth/me`
- `GET /health`

## Demo Accounts
Seeded accounts are stored in the database and all use the password `Hrms@12345`.

- `admin@hrms.com` - Admin
- `hr@hrms.com` - HR
- `manager@hrms.com` - Manager
- `employee@hrms.com` - Employee
- `ceo@hrms.com` - CEO

## Run
```bash
cd Backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Database
- Default local database: `postgresql+psycopg://postgres:postgres@localhost:5432/hrms`
- Override with `DATABASE_URL` for a different PostgreSQL host/user/password/database
- The app creates tables and seeds the initial Phase 1 login accounts on startup
