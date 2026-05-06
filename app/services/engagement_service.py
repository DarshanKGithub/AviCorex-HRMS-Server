from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import Tuple, List, Optional
from fastapi import HTTPException, status

from app.db.models import HelpdeskTicket, Announcement
from app.schemas.engagement import HelpdeskTicketCreate, AnnouncementCreate

def create_ticket(payload: HelpdeskTicketCreate, db: Session) -> HelpdeskTicket:
    ticket = HelpdeskTicket(**payload.model_dump())
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    return ticket

def get_tickets(
    db: Session,
    employee_id: Optional[str] = None,
    category: Optional[str] = None,
    page: int = 1,
    size: int = 20
) -> Tuple[List[HelpdeskTicket], int]:
    query = db.query(HelpdeskTicket)
    if employee_id:
        query = query.filter(HelpdeskTicket.employee_id == employee_id)
    if category:
        query = query.filter(HelpdeskTicket.category == category)
    
    total = query.count()
    items = query.order_by(desc(HelpdeskTicket.created_at)).offset((page - 1) * size).limit(size).all()
    return items, total

def update_ticket_status(ticket_id: str, new_status: str, assigned_to: str, db: Session) -> HelpdeskTicket:
    ticket = db.query(HelpdeskTicket).filter(HelpdeskTicket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")
    
    ticket.status = new_status
    if assigned_to:
        ticket.assigned_to = assigned_to
        
    db.commit()
    db.refresh(ticket)
    return ticket

def create_announcement(payload: AnnouncementCreate, db: Session) -> Announcement:
    ann = Announcement(**payload.model_dump())
    db.add(ann)
    db.commit()
    db.refresh(ann)
    return ann

def get_announcements(
    db: Session,
    page: int = 1,
    size: int = 20
) -> Tuple[List[Announcement], int]:
    query = db.query(Announcement).filter(Announcement.is_active == True)
    total = query.count()
    items = query.order_by(desc(Announcement.priority), desc(Announcement.created_at)).offset((page - 1) * size).limit(size).all()
    return items, total
