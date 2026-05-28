"""Appointment request/response schemas."""

from datetime import datetime, date, timezone
from pydantic import BaseModel, field_validator
from typing import Optional


class AppointmentCreate(BaseModel):
    customer_id: int
    service_type_id: int
    technician_id: Optional[int] = None  # auto-assigned if not specified
    scheduled_start: datetime
    source: str = "dashboard"
    address: Optional[str] = None
    notes: Optional[str] = None


class AppointmentUpdate(BaseModel):
    technician_id: Optional[int] = None
    scheduled_start: Optional[datetime] = None
    status: Optional[str] = None
    address: Optional[str] = None
    notes: Optional[str] = None
    problem_description: Optional[str] = None


class AppointmentResponse(BaseModel):
    id: int
    customer_id: int
    technician_id: Optional[int] = None
    service_type_id: int
    scheduled_start: datetime
    scheduled_end: datetime
    status: str
    source: str
    address: Optional[str] = None
    notes: Optional[str] = None
    problem_description: Optional[str] = None
    media_urls: Optional[list] = None
    calendar_token: str
    calendar_links_sent: bool
    recurring_schedule_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    # Nested details (populated when needed)
    customer_name: Optional[str] = None
    technician_name: Optional[str] = None
    service_name: Optional[str] = None

    model_config = {"from_attributes": True}

    @field_validator("scheduled_start", "scheduled_end", "created_at", "updated_at", mode="before")
    @classmethod
    def ensure_utc(cls, v):
        """Naive datetimes from the DB are UTC — tag them so the browser converts correctly."""
        if isinstance(v, datetime) and v.tzinfo is None:
            return v.replace(tzinfo=timezone.utc)
        return v


class AvailabilityRequest(BaseModel):
    service_type_id: int
    start_date: date
    end_date: date
    technician_id: Optional[int] = None


class TimeSlot(BaseModel):
    start: datetime
    end: datetime
    technician_ids: list[int]  # available technicians for this slot


class AvailabilityResponse(BaseModel):
    service_type_id: int
    date: date
    slots: list[TimeSlot]
