"""Simple helper to check Employee presence in the backend DB.

Usage:
  python tools/check_employee.py --id b5375da9-feab-49d8-841c-f092c804be9b

It uses the same SQLAlchemy settings as the app.
"""
import argparse
from app.db.database import SessionLocal
from app.db.models import Employee


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--id", dest="employee_id", required=False, help="Employee ID to check")
    args = p.parse_args()

    with SessionLocal() as db:
        if args.employee_id:
            emp = db.query(Employee).filter(Employee.id == args.employee_id).first()
            if emp:
                print(f"FOUND: id={emp.id} full_name={emp.full_name} email={emp.email} is_active={emp.is_active}")
            else:
                print(f"NOT FOUND: employee id {args.employee_id}")
        else:
            rows = db.query(Employee).limit(20).all()
            if not rows:
                print("No employees found in the database.")
                return
            print("First 20 employees:")
            for e in rows:
                print(f"- id={e.id} full_name={e.full_name} email={e.email} is_active={e.is_active}")


if __name__ == '__main__':
    main()
