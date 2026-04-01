"""Service type request/response schemas."""

from pydantic import BaseModel
from typing import Optional


class ServiceTypeCreate(BaseModel):
    name: str
    category: str
    description: Optional[str] = None
    duration_minutes: int
    base_price: Optional[float] = None


class ServiceTypeUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    duration_minutes: Optional[int] = None
    base_price: Optional[float] = None
    is_active: Optional[bool] = None


class ServiceTypeResponse(BaseModel):
    id: int
    name: str
    category: str
    description: Optional[str] = None
    duration_minutes: int
    base_price: Optional[float] = None
    is_active: bool

    model_config = {"from_attributes": True}
