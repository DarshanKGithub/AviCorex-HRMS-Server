import sys
from pathlib import Path

backend_dir = Path("/home/darshan-kshetri/Desktop/Client_Works/HRMS/Backend")
sys.path.append(str(backend_dir))

from app.db.database import SessionLocal
from app.db.models import User, Employee
from app.services.leave_service import get_leave_balances

with SessionLocal() as db:
    u = db.query(Employee).first()
    if u:
        print("Employee ID:", u.id)
        b = get_leave_balances(u.id, db)
        print("Balances count:", len(b))
        if b:
            print("First balance:", b[0].granted_days, b[0].balance_days)
    else:
        print("No user found")
