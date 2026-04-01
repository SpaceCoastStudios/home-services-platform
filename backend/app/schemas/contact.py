"""Contact form submission schemas."""

from datetime import datetime, date
from pydantic import BaseModel, EmailStr
from typing import Optional


class ContactFormSubmit(BaseModel):
    """Public-facing schema for website contact form submissions."""
    name: str
    email: EmailStr
    phone: Optional[str] = None
    service_requested: Optional[str] = None
    message: str
    preferred_date: Optional[date] = None
    preferred_time: Optional[str] = None


class ContactSubmissionResponse(BaseModel):
    id: int
    customer_id: Optional[int] = None
    name: str
    email: str
    phone: Optional[str] = None
    service_requested: Optional[str] = None
    message: str
    preferred_date: Optional[date] = None
    preferred_time: Optional[str] = None
    ai_response: Optional[str] = None
    ai_suggested_slots: Optional[list] = None
    status: str
    appointment_id: Optional[int] = None
    responded_at: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ContactSubmissionUpdate(BaseModel):
    status: Optional[str] = None
    notes: Optional[str] = None


class ManualResponseRequest(BaseModel):
    message: str
    send_email: bool = True
    send_sms: bool = False
