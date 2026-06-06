import sys
from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from app.db.models import Timesheet

db = SessionLocal()
try:
    ts = db.query(Timesheet).all()
    for t in ts:
        print(f"ID: {t.id}, Date: {t.date}, Desc: {t.task_description}")
    print(f"Total: {len(ts)}")
except Exception as e:
    print(f"Error: {e}")
