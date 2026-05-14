import sys
from pathlib import Path

# Ensure imports work regardless of where this script is executed from.
backend_dir = Path(__file__).resolve().parent
if str(backend_dir) not in sys.path:
    sys.path.append(str(backend_dir))

from sqlalchemy import inspect, text
from app.db.database import engine
from app.db.models import Base

def backfill_columns():
    inspector = inspect(engine)
    with engine.begin() as conn:
        for table_name, table in Base.metadata.tables.items():
            if not inspector.has_table(table_name):
                print(f"Table {table_name} does not exist, skipping (create_all will handle it).")
                continue
                
            existing_columns = {col['name'] for col in inspector.get_columns(table_name)}
            for column in table.columns:
                if column.name not in existing_columns:
                    col_type = column.type.compile(engine.dialect)
                    nullable = "NULL" if column.nullable else "NOT NULL"
                    default_clause = ""
                    # We just use basic types for alter table to avoid complex default expressions
                    print(f"Adding missing column: {table_name}.{column.name} type: {col_type}")
                    try:
                        # Use a safe conditional add for Postgres; fallback to plain ALTER otherwise
                        if engine.dialect.name == 'postgresql':
                            conn.execute(text(f"ALTER TABLE {table_name} ADD COLUMN IF NOT EXISTS {column.name} {col_type}"))
                        else:
                            conn.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {column.name} {col_type}"))
                    except Exception as e:
                        print(f"Failed to add column {table_name}.{column.name}: {e}")

if __name__ == "__main__":
    backfill_columns()
    print("Backfill complete.")
