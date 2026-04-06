"""Technician model."""

from sqlalchemy import String, Boolean, JSON, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Technician(Base):
    __tablename__ = "technicians"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    business_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("businesses.id"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    skills: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Relationships
    business = relationship("Business", back_populates="technicians")
    appointments = relationship("Appointment", back_populates="technician")
    blocked_times = relationship("BlockedTime", back_populates="technician")
    recurring_schedules = relationship("RecurringSchedule", back_populates="technician")
    oncall_rotations    = relationship("OnCallRotation", back_populates="technician")
    oncall_overrides    = relationship("OnCallOverride", back_populates="technician")
