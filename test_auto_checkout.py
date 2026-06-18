import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parent
if str(backend_dir) not in sys.path:
    sys.path.append(str(backend_dir))

from app.db.database import SessionLocal
from app.services.attendance_service import run_auto_checkout_job

def test():
    print("Testing auto-checkout job...")
    with SessionLocal() as db:
        run_auto_checkout_job(db)
    print("Test complete.")

if __name__ == '__main__':
    test()
