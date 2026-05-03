from pydantic import BaseModel


class AuditLogPublic(BaseModel):
    id: str
    actor_id: str | None = None
    action: str
    object_type: str
    object_id: str | None = None
    data: str | None = None
    created_at: str


class PaginatedAuditLogs(BaseModel):
    items: list[AuditLogPublic]
    total: int
    page: int
    size: int
