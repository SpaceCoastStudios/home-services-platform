"""Business hours and blocked time schemas."""

from datetime import datetime, time
from pydantic import BaseModel
from typing import Optional


class BusinessHoursEntry(BaseModel):
    day_of_week: int  # 0=Monday, 6=Sunday
    open_time: time
    close_time: time
    is_active: bool = True


class BusinessHoursUpdate(BaseModel):
    hours: list[BusinessHoursEntry]


class BusinessHoursResponse(BaseModel):
    id: int
    day_of_week: int
    open_time: time
    close_time: time
    is_active: bool

    model_config = {"from_attributes": True}


class BlockedTimeCreate(BaseModel):
    technician_id: Optional[int] = None  # NULL = entire business
    start_datetime: datetime
    end_datetime: datetime
    reason: Optional[str] = None


class BlockedTimeResponse(BaseModel):
    id: int
    technician_id: Optional[int] = None
    start_datetime: datetime
    end_datetime: datetime
    reason: Optional[str] = None

    model_config = {"from_attributes": True}


class SystemSettingResponse(BaseModel):
    key: str
    value: str
    description: Optional[str] = None

    model_config = {"from_attributes": True}


class SystemSettingUpdate(BaseModel):
    value: str
