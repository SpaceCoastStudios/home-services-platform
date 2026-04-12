"""Business (tenant) model — represents each client business on the platform."""

from datetime import datetime, timezone
from sqlalchemy import String, Text, Boolean, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Business(Base):
    __tablename__ = "businesses"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    # e.g. "peak-hvac" — used in public API paths and subdomains

    # Contact & branding
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    website: Mapped[str | None] = mapped_column(String(255), nullable=True)
    logo_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    brand_color: Mapped[str | None] = mapped_column(String(7), nullable=True)
    # e.g. "#2563eb"

    # Industry / type
    industry: Mapped[str | None] = mapped_column(String(100), nullable=True)
    # e.g. "hvac", "landscaping", "plumbing"

    # Twilio — each business gets their own phone number
    twilio_phone_number: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # Email sending — the "From" address used when emailing this business's customers.
    # Should be a verified sender on the business's own domain (e.g. info@peakhvac.com).
    # Falls back to the platform SENDGRID_FROM_EMAIL setting if not set.
    from_email: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # AI agent persona — customized per business
    ai_agent_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    # e.g. "Peak Assistant"
    ai_system_prompt: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Custom instructions for the AI agent for this business

    # AI auto-responder mode for contact form submissions:
    #   "auto_send"  — AI response is sent immediately (default)
    #   "draft_only" — AI drafts a response but staff must approve before sending
    ai_response_mode: Mapped[str] = mapped_column(String(20), default="auto_send")

    # Plan / status
    plan: Mapped[str] = mapped_column(String(20), default="full")
    # "full" = we host their whole site, "mini" = API/connectors only
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    admin_users = relationship("AdminUser", back_populates="business")
    customers = relationship("Customer", back_populates="business")
    service_types = relationship("ServiceType", back_populates="business")
    technicians = relationship("Technician", back_populates="business")
    business_hours = relationship("BusinessHours", back_populates="business")
    blocked_times = relationship("BlockedTime", back_populates="business")
    appointments = relationship("Appointment", back_populates="business")
    inquiry_logs = relationship("InquiryLog", back_populates="business")
    contact_submissions = relationship("ContactSubmission", back_populates="business")
    settings = relationship("SystemSetting", back_populates="business")
    recurring_schedules = relationship("RecurringSchedule", back_populates="business")
    oncall_config       = relationship("OnCallConfig", back_populates="business", uselist=False)
