"""RecurringSchedule model — stores a repeating appointment pattern for a customer."""

from datetime import datetime, date, time, timezone
from sqlalchemy import String, Text, DateTime, Date, Time, Integer, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

FREQUENCIES = ("weekly", "biweekly", "monthly")


class RecurringSchedule(Base):
    __tablename__ = "recurring_schedules"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    business_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("businesses.id"), nullable=False, index=True
    )
    customer_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("customers.id"), nullable=False
    )
    service_type_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("service_types.id"), nullable=False
    )
    technician_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("technicians.id"), nullable=True
    )

    # Recurrence pattern
    frequency: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # "weekly" | "biweekly" | "monthly"

    # For weekly/biweekly: day of week (0=Monday … 6=Sunday)
    preferred_day_of_week: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # For monthly: day of month (1–28 — capped at 28 to avoid month-end issues)
    preferred_day_of_month: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Preferred start time of day for the appointment
    preferred_time: Mapped[time] = mapped_column(Time, nullable=False)

    # When the series starts and (optionally) ends
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    # How many days ahead to pre-generate appointments
    lookahead_days: Mapped[int] = mapped_column(Integer, default=60, nullable=False)

    # Optional job details that apply to every appointment in the series
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    business = relationship("Business", back_populates="recurring_schedules")
    customer = relationship("Customer", back_populates="recurring_schedules")
    service_type = relationship("ServiceType", back_populates="recurring_schedules")
    technician = relationship("Technician", back_populates="recurring_schedules")
    appointments = relationship("Appointment", back_populates="recurring_schedule")
