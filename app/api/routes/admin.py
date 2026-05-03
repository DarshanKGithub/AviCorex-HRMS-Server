from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.audit import PaginatedAuditLogs, AuditLogPublic
from app.services.audit_service import list_audit_logs
from app.services.auth_service import get_user_from_token

security = HTTPBearer(auto_error=False)
router = APIRouter()


@router.get('/audit-logs', response_model=PaginatedAuditLogs)
def audit_logs(page: int = 1, size: int = 20, object_type: str | None = None, actor_id: str | None = None,
               credentials: HTTPAuthorizationCredentials | None = Depends(security), db: Session = Depends(get_db)):
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Not authenticated')

    user = get_user_from_token(credentials.credentials, db=db)
    if user.role != 'Admin':
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Insufficient privileges')

    items, total = list_audit_logs(db=db, page=page, size=size, object_type=object_type, actor_id=actor_id)
    return PaginatedAuditLogs(
        items=[AuditLogPublic(
            id=a.id,
            actor_id=a.actor_id,
            action=a.action,
            object_type=a.object_type,
            object_id=a.object_id,
            data=a.data,
            created_at=a.created_at.isoformat(),
        ) for a in items],
        total=total,
        page=page,
        size=size,
    )
