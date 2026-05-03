from typing import Tuple
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.db.models import AuditLog


def list_audit_logs(db: Session, page: int = 1, size: int = 20, object_type: str | None = None,
                    actor_id: str | None = None) -> Tuple[list[AuditLog], int]:
    stmt = select(AuditLog)
    if object_type:
        stmt = stmt.where(AuditLog.object_type == object_type)
    if actor_id:
        stmt = stmt.where(AuditLog.actor_id == actor_id)

    total = db.scalar(select(func.count()).select_from(stmt.subquery()))
    items = db.scalars(stmt.order_by(AuditLog.created_at.desc()).offset((page - 1) * size).limit(size)).all()
    return items, int(total or 0)
