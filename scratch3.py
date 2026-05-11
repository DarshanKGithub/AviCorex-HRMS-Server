import sys
from pathlib import Path

backend_dir = Path("/home/darshan-kshetri/Desktop/Client_Works/HRMS/Backend")
sys.path.append(str(backend_dir))

from app.db.models import Base
print("Tables in Base:")
for table_name in Base.metadata.tables.keys():
    if "recruit" in table_name or "job" in table_name or "candid" in table_name or "interview" in table_name or "offer" in table_name or "asset" in table_name or "org" in table_name or "survey" in table_name:
        print(table_name)
