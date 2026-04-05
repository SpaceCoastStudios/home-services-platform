"""Schemas for RecurringSchedule create / update / response."""

from datetime import date, time, datetime
from pydantic import BaseModel, field_validator
from typing import Optional


class RecurringScheduleCreate(BaseModel):
    customer_id: int
    service_type_id: int
    technician_id: Optional[int] = None
    frequency: str  # "weekly" | "biweekly" | "monthly"
    preferred_day_of_week: Optional[int] = None   # 0=Mon … 6=Sun (weekly/biweekly)
    preferred_day_of_month: Optional[int] = None  # 1–28 (monthly)
    preferred_time: time
    start_date: date
    end_date: Optional[date] = None
    lookahead_days: int = 60
    address: Optional[str] = None
    notes: Optional[str] = None

    @field_validator("frequency")
    @classmethod
    def validate_frequency(cls, v):
        if v not in ("weekly", "biweekly", "monthly"):
            raise ValueError("frequency must be 'weekly', 'biweekly', or 'monthly'")
        return v

    @field_validator("preferred_day_of_week")
    @classmethod
    def validate_dow(cls, v):
        if v is not None and not (0 <= v <= 6):
            raise ValueError("preferred_day_of_week must be 0–6")
        return v

    @field_validator("preferred_day_of_month")
    @classmethod
    def validate_dom(cls, v):
        if v is not None and not (1 <= v <= 28):
            raise ValueError("preferred_day_of_month must be 1–28")
        return v


class RecurringScheduleUpdate(BaseModel):
    technician_id: Optional[int] = None
    frequency: Optional[str] = None
    preferred_day_of_week: Optional[int] = None
    preferred_day_of_month: Optional[int] = None
    preferred_time: Optional[time] = None
    end_date: Optional[date] = None
    lookahead_days: Optional[int] = None
    address: Optional[str] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None


class RecurringScheduleResponse(BaseModel):
    id: int
    business_id: int
    customer_id: int
    service_type_id: int
    technician_id: Optional[int] = None
    frequency: str
    preferred_day_of_week: Optional[int] = None
    preferred_day_of_month: Optional[int] = None
    preferred_time: time
    start_date: date
    end_date: Optional[date] = None
    lookahead_days: int
    address: Optional[str] = None
    notes: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    # Denormalised display names
    customer_name: Optional[str] = None
    service_name: Optional[str] = None
    technician_name: Optional[str] = None

    model_config = {"from_attributes": True}
