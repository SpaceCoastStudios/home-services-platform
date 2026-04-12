"""
On-call routing models.

OnCallConfig    — per-business settings: enabled, after-hours window,
                  rotation type, fallback contact.
OnCallRotation  — individual rotation entries (day-of-week OR rolling weekly).
OnCallOverride  — temporary manual override (expires automatically).
"""

from datetime import datetime, date, time, timezone
from sqlalchemy import (
    Integer, String, Boolean, DateTime, Date, Time, Text, Numeric, ForeignKey
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class OnCallConfig(Base):
    """One row per business — master on-call settings."""
    __tablename__ = "oncall_configs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    business_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("businesses.id"), nullable=False, unique=True, index=True
    )

    # Master switch
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # After-hours window — calls outside business hours route to on-call
    # These times are stored in the business's local time zone
    after_hours_start: Mapped[time] = mapped_column(Time, nullable=False, default=time(18, 0))   # 6:00 PM
    after_hours_end: Mapped[time] = mapped_column(Time, nullable=False, default=time(8, 0))     # 8:00 AM

    # Emergency window — a tighter window for urgent calls (optional)
    emergency_window_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    emergency_window_start: Mapped[time | None] = mapped_column(Time, nullable=True)
    emergency_window_end: Mapped[time | None] = mapped_column(Time, nullable=True)

    # Rotation type for this business
    # "day_of_week"   — same tech each Monday, different each Tuesday, etc.
    # "weekly_rolling"— rotates through techs week by week
    rotation_type: Mapped[str] = mapped_column(
        String(20), nullable=False, default="day_of_week"
    )

    # Reference Monday for rolling rotation week calculation
    rolling_start_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    # Emergency fee — shown to customer via SMS before dispatching
    emergency_fee_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    emergency_fee: Mapped[float | None] = mapped_column(Numeric(8, 2), nullable=True)
    # e.g. 150.00 → AI tells customer "An emergency fee of $150 applies"

    # Fallback: if no on-call tech is found, route here
    fallback_phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    fallback_name: Mapped[str | None] = mapped_column(String(100), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    business   = relationship("Business", back_populates="oncall_config")
    rotations  = relationship("OnCallRotation", back_populates="config",
                              cascade="all, delete-orphan")
    overrides  = relationship("OnCallOverride", back_populates="config",
                              cascade="all, delete-orphan")


class OnCallRotation(Base):
    """
    One entry per slot in the rotation.

    day_of_week mode  → set day_of_week (0=Mon … 6=Sun), leave position NULL
    weekly_rolling mode → set position (0, 1, 2, …), leave day_of_week NULL
    """
    __tablename__ = "oncall_rotations"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    config_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("oncall_configs.id"), nullable=False, index=True
    )
    technician_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("technicians.id"), nullable=False
    )

    # day_of_week mode: 0=Monday … 6=Sunday
    day_of_week: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # weekly_rolling mode: 0-indexed position in the cycle
    position: Mapped[int | None] = mapped_column(Integer, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    config     = relationship("OnCallConfig", back_populates="rotations")
    technician = relationship("Technician", back_populates="oncall_rotations")


class OnCallOverride(Base):
    """
    Temporary manual override — who is on-call right now regardless of rotation.
    Expires automatically at expires_at; defaults to 24 hours from creation.
    """
    __tablename__ = "oncall_overrides"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    config_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("oncall_configs.id"), nullable=False, index=True
    )
    technician_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("technicians.id"), nullable=False
    )
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    config     = relationship("OnCallConfig", back_populates="overrides")
    technician = relationship("Technician", back_populates="oncall_overrides")
