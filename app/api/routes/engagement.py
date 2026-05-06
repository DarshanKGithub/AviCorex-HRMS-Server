from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel

from app.core.rbac import get_current_user, has_permission, require_permissions
from app.db.database import get_db
from app.db.models import User
from app.schemas.engagement import (
    HelpdeskTicketCreate,
    HelpdeskTicketPublic,
    PaginatedHelpdeskTickets,
    AnnouncementCreate,
    AnnouncementPublic,
    PaginatedAnnouncements
)
from app.services.engagement_service import (
    create_ticket,
    get_tickets,
    update_ticket_status,
    create_announcement,
    get_announcements
)

router = APIRouter()

# --- Helpdesk Routes ---

@router.post('/tickets', response_model=HelpdeskTicketPublic)
def submit_ticket(
    payload: HelpdeskTicketCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if payload.employee_id != user.id and not has_permission(user.role, 'manage_helpdesk'):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot create tickets for others")
    
    return HelpdeskTicketPublic.model_validate(create_ticket(payload, db))

@router.get('/tickets', response_model=PaginatedHelpdeskTickets)
def list_tickets(
    employee_id: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if employee_id and employee_id != user.id and not has_permission(user.role, 'manage_helpdesk'):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot view other's tickets")

    if not employee_id and not has_permission(user.role, 'manage_helpdesk'):
        employee_id = user.id

    items, total = get_tickets(db, employee_id, category, page, size)
    return PaginatedHelpdeskTickets(
        items=[HelpdeskTicketPublic.model_validate(i) for i in items],
        total=total,
        page=page,
        size=size
    )

class TicketStatusUpdate(BaseModel):
    status: str

@router.put('/tickets/{ticket_id}/status', response_model=HelpdeskTicketPublic)
def change_ticket_status(
    ticket_id: str,
    payload: TicketStatusUpdate,
    user: User = Depends(require_permissions('manage_helpdesk')),
    db: Session = Depends(get_db)
):
    return HelpdeskTicketPublic.model_validate(update_ticket_status(ticket_id, payload.status, user.id, db))


# --- Announcement Routes ---

class AnnouncementRequest(BaseModel):
    title: str
    content: str
    priority: Optional[str] = 'Normal'

@router.post('/announcements', response_model=AnnouncementPublic)
def post_announcement(
    payload: AnnouncementRequest,
    user: User = Depends(require_permissions('manage_announcements')),
    db: Session = Depends(get_db)
):
    ann_create = AnnouncementCreate(
        title=payload.title,
        content=payload.content,
        priority=payload.priority,
        author_id=user.id
    )
    return AnnouncementPublic.model_validate(create_announcement(ann_create, db))

@router.get('/announcements', response_model=PaginatedAnnouncements)
def list_active_announcements(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    items, total = get_announcements(db, page, size)
    return PaginatedAnnouncements(
        items=[AnnouncementPublic.model_validate(i) for i in items],
        total=total,
        page=page,
        size=size
    )
