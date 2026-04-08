"""SMS conversation model — stores per-business, per-customer-phone thread state."""

from datetime import datetime, timezone
from sqlalchemy import Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class SmsConversation(Base):
    __tablename__ = "sms_conversations"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    business_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("businesses.id"), nullable=False, index=True
    )
    customer_phone: Mapped[str] = mapped_column(
        String(20), nullable=False, index=True
    )

    # Learned from the conversation — may be None until the AI collects it
    customer_name: Mapped[str | None] = mapped_column(String(200), nullable=True)

    # JSON array of message turns:
    # [{"role": "user"|"assistant", "content": "...", "ts": "ISO8601"}, ...]
    messages: Mapped[list] = mapped_column(JSON, nullable=False, default=list)

    # Status lifecycle: active → booked | escalated | closed
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")

    # Set if the AI successfully created a booking
    appointment_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("appointments.id"), nullable=True
    )

    last_message_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    business = relationship("Business", foreign_keys=[business_id])
    appointment = relationship("Appointment", foreign_keys=[appointment_id])
