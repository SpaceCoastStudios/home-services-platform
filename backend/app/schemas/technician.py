"""Technician request/response schemas."""

from pydantic import BaseModel
from typing import Optional


class TechnicianCreate(BaseModel):
    name: str
    phone: Optional[str] = None
    email: Optional[str] = None
    skills: list[str]  # e.g. ["plumbing", "hvac"]


class TechnicianUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    skills: Optional[list[str]] = None
    is_active: Optional[bool] = None


class TechnicianResponse(BaseModel):
    id: int
    name: str
    phone: Optional[str] = None
    email: Optional[str] = None
    skills: list[str]
    is_active: bool

    model_config = {"from_attributes": True}
