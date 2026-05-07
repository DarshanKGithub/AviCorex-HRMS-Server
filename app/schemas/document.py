from pydantic import BaseModel
from datetime import datetime

class EmployeeDocumentPublic(BaseModel):
    id: str
    employee_id: str
    document_type: str
    file_name: str
    uploaded_by: str
    uploaded_at: datetime
