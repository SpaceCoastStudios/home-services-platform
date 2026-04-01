"""Notification log model."""

from datetime import datetime, timezone
from sqlalchemy import Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class NotificationLog(Base):
    __tablename__ = "notification_logs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    appointment_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("appointments.id"), nullable=False
    )
    type: Mapped[str] = mapped_column(String(10), nullable=False)  # sms, email
    event: Mapped[str] = mapped_column(
        String(30), nullable=False
    )  # confirmation, reminder_24h, reminder_1h, cancellation, reschedule
    sent_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # sent, failed, delivered

    # Relationships
    appointment = relationship("Appointment", back_populates="notifications")
