# DB Migrations (Alembic)

This project uses a lightweight Alembic scaffold placed at `Backend/alembic/` for schema migrations.

Quick steps to run migrations locally or in CI:

1. Ensure the Python environment and dependencies are installed and `DATABASE_URL` env var points to your DB.

2. Run migrations:

```bash
source .venv/bin/activate
export DATABASE_URL=postgresql+psycopg://user:pass@host/dbname
alembic -c Backend/alembic.ini upgrade head
```

Notes for Render (production):
- Add a deploy step that runs Alembic migrations before starting the app process.
- Do NOT enable `AUTO_APPLY_SCHEMA_CHANGES` in production regularly; prefer migrations.

If you want, I can add an `alembic` entry in `requirements.txt` and a simple CI snippet to run migrations.
