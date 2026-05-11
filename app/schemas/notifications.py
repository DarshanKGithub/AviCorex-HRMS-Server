"""
Pydantic schemas for Notification Automation module
"""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


# Notification Template Schemas
class NotificationTemplateBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=500)
    event_type: str = Field(..., min_length=1, max_length=100)
    channel: str = Field(..., description="email, sms, in_app, push")
    subject: Optional[str] = Field(None, max_length=200)
    body: str = Field(..., min_length=1, max_length=2000, description="Template with {variable} placeholders")
    is_active: bool = Field(default=True)


class NotificationTemplateCreate(NotificationTemplateBase):
    pass


class NotificationTemplateUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    subject: Optional[str] = None
    body: Optional[str] = None
    is_active: Optional[bool] = None


class NotificationTemplatePublic(NotificationTemplateBase):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Notification Schemas
class NotificationBase(BaseModel):
    event_type: str = Field(..., max_length=100)
    channel: str = Field(..., description="email, sms, in_app, push")
    subject: Optional[str] = Field(None, max_length=200)
    message: str = Field(..., max_length=2000)
    data: Optional[str] = Field(None, max_length=2000, description="JSON metadata")


class NotificationCreate(NotificationBase):
    recipient_id: str
    template_id: Optional[str] = None


class NotificationUpdate(BaseModel):
    status: Optional[str] = None
    read_at: Optional[datetime] = None


class NotificationPublic(NotificationBase):
    id: str
    recipient_id: str
    template_id: Optional[str]
    status: str
    read_at: Optional[datetime]
    sent_at: Optional[datetime]
    error_message: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class NotificationFilter(BaseModel):
    status: Optional[str] = None
    channel: Optional[str] = None
    event_type: Optional[str] = None
    read: Optional[bool] = None
    limit: int = Field(default=50, le=500)
    offset: int = Field(default=0, ge=0)


# Notification Preference Schemas
class NotificationPreferenceBase(BaseModel):
    email_enabled: bool = Field(default=True)
    sms_enabled: bool = Field(default=False)
    in_app_enabled: bool = Field(default=True)
    push_enabled: bool = Field(default=True)
    quiet_hours_start: Optional[str] = Field(None, pattern="^([0-1][0-9]|2[0-3]):[0-5][0-9]$")
    quiet_hours_end: Optional[str] = Field(None, pattern="^([0-1][0-9]|2[0-3]):[0-5][0-9]$")


class NotificationPreferenceUpdate(NotificationPreferenceBase):
    pass


class NotificationPreferencePublic(NotificationPreferenceBase):
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Bulk Notification Schema
class BulkNotificationCreate(BaseModel):
    recipient_ids: list[str]
    event_type: str
    channel: str
    template_id: Optional[str] = None
    subject: Optional[str] = None
    message: str
    data: Optional[str] = None


# Notification Stats
class NotificationStats(BaseModel):
    unread_count: int
    total_count: int
    by_channel: dict = {}  # {"email": 5, "in_app": 10}
    by_status: dict = {}   # {"sent": 10, "pending": 2, "failed": 1}
