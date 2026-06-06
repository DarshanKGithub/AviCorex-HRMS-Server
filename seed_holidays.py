import sys
import os

# Add Backend to sys path
sys.path.append('/home/darshan-kshetri/Desktop/Client_Works/HRMS/Backend')

from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from app.db.models import Holiday
from datetime import date

holidays_2026 = [
    {"name": "Republic Day", "date": date(2026, 1, 26)},
    {"name": "Maha Shivaratri", "date": date(2026, 2, 14)},
    {"name": "Holi", "date": date(2026, 3, 3)},
    {"name": "Good Friday", "date": date(2026, 4, 3)},
    {"name": "Id-ul-Fitr", "date": date(2026, 3, 20)},
    {"name": "Independence Day", "date": date(2026, 8, 15)},
    {"name": "Mahatma Gandhi Birthday", "date": date(2026, 10, 2)},
    {"name": "Dussehra", "date": date(2026, 10, 19)},
    {"name": "Diwali (Deepavali)", "date": date(2026, 11, 8)},
    {"name": "Guru Nanak's Birthday", "date": date(2026, 11, 24)},
    {"name": "Christmas Day", "date": date(2026, 12, 25)}
]

def seed_holidays():
    db: Session = SessionLocal()
    try:
        count = 0
        for h in holidays_2026:
            # Check if exists
            existing = db.query(Holiday).filter(Holiday.holiday_date == h['date']).first()
            if not existing:
                new_holiday = Holiday(name=h['name'], holiday_date=h['date'], is_public=True)
                db.add(new_holiday)
                count += 1
        db.commit()
        print(f"Successfully added {count} new holidays for 2026!")
    finally:
        db.close()

if __name__ == "__main__":
    seed_holidays()
