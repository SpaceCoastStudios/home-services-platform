"""Notification template model — per-business editable SMS and email templates."""

from datetime import datetime, timezone
from sqlalchemy import Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


# ---------------------------------------------------------------------------
# Event types and channels
# ---------------------------------------------------------------------------
# event_type values:
#   "confirmation"  — sent immediately when an appointment is booked
#   "reminder_24h"  — sent ~24 hours before the appointment
#
# channel values:
#   "sms"   — plain text body only
#   "email" — subject + plain text body (wrapped in branded HTML envelope)
# ---------------------------------------------------------------------------

# Default template bodies — used as fallback when a business has no saved template
DEFAULTS: dict[tuple[str, str], dict] = {
    ("confirmation", "sms"): {
        "subject": None,
        "body": (
            "Hi {{customer_name}}! Your {{service_name}} appointment is confirmed "
            "for {{date_time}} with {{technician_name}}. "
            "Add to calendar: {{calendar_link}}. "
            "Reply STOP to opt out."
        ),
    },
    ("confirmation", "email"): {
        "subject": "Your {{service_name}} Appointment is Confirmed",
        "body": (
            "Hi {{customer_name}},\n\n"
            "Your {{service_name}} appointment has been confirmed.\n\n"
            "Date & Time: {{date_time}}\n"
            "Technician: {{technician_name}}\n"
            "Location: {{address}}\n\n"
            "Use the calendar buttons below to add this to your calendar.\n\n"
            "Thank you for choosing {{business_name}}!"
        ),
    },
    ("reminder_24h", "sms"): {
        "subject": None,
        "body": (
            "Reminder: Your {{service_name}} appointment with {{business_name}} "
            "is tomorrow at {{date_time}}. "
            "Questions? Call {{business_phone}}. "
            "Reply STOP to opt out."
        ),
    },
    ("reminder_24h", "email"): {
        "subject": "Reminder: Your {{service_name}} appointment is coming up",
        "body": (
            "Hi {{customer_name}},\n\n"
            "This is a friendly reminder about your upcoming appointment.\n\n"
            "Service: {{service_name}}\n"
            "Date & Time: {{date_time}}\n"
            "Location: {{address}}\n\n"
            "Need to reschedule or have questions? "
            "Reply to this email or call {{business_phone}}.\n\n"
            "Thank you,\n{{business_name}}"
        ),
    },
}

# Available tokens per event type — shown in the dashboard UI
TOKENS = {
    "all": [
        ("{{customer_name}}", "Customer's first name"),
        ("{{business_name}}", "Business name"),
        ("{{service_name}}", "Service type"),
        ("{{date_time}}", "Appointment date and time"),
        ("{{business_phone}}", "Business phone number"),
        ("{{address}}", "Appointment address"),
        ("{{technician_name}}", "Assigned technician"),
    ],
    "confirmation": [
        ("{{calendar_link}}", "Add-to-calendar link (email/SMS)"),
    ],
}


class NotificationTemplate(Base):
    __tablename__ = "notification_templates"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    business_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("businesses.id"), nullable=False, index=True
    )
    event_type: Mapped[str] = mapped_column(
        String(30), nullable=False
    )  # "confirmation" | "reminder_24h"
    channel: Mapped[str] = mapped_column(
        String(10), nullable=False
    )  # "sms" | "email"

    subject: Mapped[str | None] = mapped_column(
        String(300), nullable=True
    )  # email subject line (None for SMS)
    body: Mapped[str] = mapped_column(
        Text, nullable=False
    )  # SMS body or email plain-text body

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    business = relationship("Business", foreign_keys=[business_id])
