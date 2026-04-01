"""Blocked time model."""

from datetime import datetime, timezone
from sqlalchemy import Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class BlockedTime(Base):
    __tablename__ = "blocked_times"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    business_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("businesses.id"), nullable=False, index=True
    )
    technician_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("technicians.id"), nullable=True
    )  # NULL = block for entire business
    start_datetime: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    end_datetime: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    reason: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Relationships
    business = relationship("Business", back_populates="blocked_times")
    technician = relationship("Technician", back_populates="blocked_times")
