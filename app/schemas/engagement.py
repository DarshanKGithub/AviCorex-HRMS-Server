from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict


class HelpdeskTicketBase(BaseModel):
    employee_id: str
    subject: str
    description: str
    category: Optional[str] = 'General'
    priority: Optional[str] = 'Medium'


class HelpdeskTicketCreate(HelpdeskTicketBase):
    pass


class HelpdeskTicketPublic(HelpdeskTicketBase):
    model_config = ConfigDict(from_attributes=True)
    id: str
    status: str
    assigned_to: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class PaginatedHelpdeskTickets(BaseModel):
    items: List[HelpdeskTicketPublic]
    total: int
    page: int
    size: int


class AnnouncementBase(BaseModel):
    title: str
    content: str
    priority: Optional[str] = 'Normal'
    is_active: Optional[bool] = True


class AnnouncementCreate(AnnouncementBase):
    author_id: str


class AnnouncementPublic(AnnouncementBase):
    model_config = ConfigDict(from_attributes=True)
    id: str
    author_id: str
    created_at: datetime


class PaginatedAnnouncements(BaseModel):
    items: List[AnnouncementPublic]
    total: int
    page: int
    size: int
