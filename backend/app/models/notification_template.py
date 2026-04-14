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
    ("emergency_dispatch", "sms"): {
        "subject": None,
        "body": (
            "🚨 EMERGENCY — {{business_name}}\n"
            "Customer: {{customer_name}}\n"
            "Phone: {{customer_phone}}\n"
            "Issue: {{issue_summary}}\n\n"
            "Respond immediately."
        ),
    },
    ("review_request", "sms"): {
        "subject": None,
        "body": (
            "Hi {{customer_name}}! Thank you for choosing {{business_name}}. "
            "We'd love to hear about your experience — would you mind leaving us a quick review? "
            "{{review_link}} 🙏"
        ),
    },
    ("review_request", "email"): {
        "subject": "How did we do, {{customer_name}}?",
        "body": (
            "Hi {{customer_name}},\n\n"
            "Thank you for trusting {{business_name}} with your {{service_name}}. "
            "We hope everything went smoothly!\n\n"
            "If you have a moment, we'd really appreciate a quick review — it helps other "
            "homeowners find us and helps our team improve.\n\n"
            "Leave a review: {{review_link}}\n\n"
            "Thank you so much,\n{{business_name}}"
        ),
    },
    # OTW tech prompt — sent to the technician 1 hour before the appointment
    ("otw_tech_prompt", "sms"): {
        "subject": None,
        "body": (
            "Heading to {{customer_name}} at {{address}}. "
            "Reply YES when you're on the way."
        ),
    },
    # OTW customer notification — sent to the customer when tech replies YES
    ("otw_customer", "sms"): {
        "subject": None,
        "body": (
            "Hi {{customer_name}}! Your {{business_name}} technician is on the way. "
            "Reply STOP to opt out."
        ),
    },
    # OTW complete prompt — sent back to the tech after they confirm they're on the way
    ("otw_tech_complete_prompt", "sms"): {
        "subject": None,
        "body": "Got it! Reply YES when you're finished with the job.",
    },
    # Morning kickoff — sent to the tech ~1 hour before their first appointment (never before 7 AM)
    ("otw_morning_kickoff", "sms"): {
        "subject": None,
        "body": (
            "Good morning, {{tech_name}}! You have {{appointment_count}} job(s) scheduled today. "
            "Reply YES when you're headed to your first stop: "
            "{{customer_name}} at {{address}}."
        ),
    },
    # Next stop prompt — sent between jobs after tech marks previous job complete
    ("otw_next_stop", "sms"): {
        "subject": None,
        "body": (
            "Great work! Ready for your next stop? "
            "Reply YES when you're headed to {{customer_name}} at {{address}}."
        ),
    },
    # Day complete — sent after the tech completes their last job of the day
    ("otw_day_complete", "sms"): {
        "subject": None,
        "body": "That's a wrap, {{tech_name}}! Great work today. Enjoy your evening! \U0001f31f",
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
    "otw_morning_kickoff": [
        ("{{tech_name}}", "Technician's first name"),
        ("{{appointment_count}}", "Number of jobs scheduled today"),
    ],
    "otw_day_complete": [
        ("{{tech_name}}", "Technician's first name"),
    ],
    "confirmation": [
        ("{{calendar_link}}", "Add-to-calendar link (email/SMS)"),
    ],
    "emergency_dispatch": [
        ("{{customer_phone}}", "Customer's phone number"),
        ("{{issue_summary}}", "Brief description of the emergency"),
    ],
    "review_request": [
        ("{{review_link}}", "Google review link URL"),
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
