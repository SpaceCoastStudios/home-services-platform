"""Appointment model."""

import secrets
from datetime import datetime, timezone
from sqlalchemy import Integer, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Appointment(Base):
    __tablename__ = "appointments"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    business_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("businesses.id"), nullable=False, index=True
    )
    customer_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("customers.id"), nullable=False
    )
    technician_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("technicians.id"), nullable=True
    )
    service_type_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("service_types.id"), nullable=False
    )
    scheduled_start: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    scheduled_end: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    source: Mapped[str] = mapped_column(String(20), nullable=False)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    calendar_token: Mapped[str] = mapped_column(
        String(64), unique=True, nullable=False,
        default=lambda: secrets.token_urlsafe(48)
    )
    calendar_links_sent: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    business = relationship("Business", back_populates="appointments")
    customer = relationship("Customer", back_populates="appointments")
    technician = relationship("Technician", back_populates="appointments")
    service_type = relationship("ServiceType", back_populates="appointments")
    notifications = relationship("NotificationLog", back_populates="appointment")
