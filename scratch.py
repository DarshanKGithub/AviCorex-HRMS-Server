import sys
from pathlib import Path
from sqlalchemy import text

backend_dir = Path("/home/darshan-kshetri/Desktop/Client_Works/HRMS/Backend")
sys.path.append(str(backend_dir))

from app.db.database import engine

with engine.begin() as conn:
    res = conn.execute(text("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'leave_balances'"))
    for row in res:
        print(row)
