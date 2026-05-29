"""
oncall_notifier.py — Dispatch emergency SMS alerts to the on-call technician.

Used by the SMS AI agent when it detects an emergency situation.
Looks up the current on-call technician, renders the dispatch template,
and sends an SMS via Twilio.
"""

import logging
import re
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.config import settings
from app.models.business import Business
from app.models.oncall import OnCallConfig, OnCallOverride
from app.models.technician import Technician
from app.models.notification_template import DEFAULTS

logger = logging.getLogger(__name__)

# Default dispatch SMS template (used if no custom template saved)
DISPATCH_DEFAULT = (
    "🚨 EMERGENCY — {{business_name}}\n"
    "Customer: {{customer_name}}\n"
    "Phone: {{customer_phone}}\n"
    "Address: {{address}}\n"
    "Issue: {{issue_summary}}\n\n"
    "Respond immediately."
)


def _get_active_override(config: OnCallConfig) -> Optional[OnCallOverride]:
    now = datetime.now(timezone.utc)
    for override in config.overrides:
        if override.expires_at > now:
            return override
    return None


def _business_local_now(business_id: int, db: Session):
    """Current time in the business's local timezone (defaults to America/New_York)."""
    import pytz
    from datetime import datetime, timezone
    biz = db.query(Business).filter(Business.id == business_id).first()
    tz_str = (getattr(biz, "timezone", None) or "America/New_York") if biz else "America/New_York"
    try:
        biz_tz = pytz.timezone(tz_str)
    except Exception:
        biz_tz = pytz.timezone("America/New_York")
    return datetime.now(timezone.utc).astimezone(biz_tz)


def _current_oncall_tech(business_id: int, db: Session) -> Optional[Technician]:
    """Return the on-call technician for a business right now, or None."""
    from datetime import datetime, timezone

    config = db.query(OnCallConfig).filter(
        OnCallConfig.business_id == business_id,
        OnCallConfig.is_enabled == True,
    ).first()

    if not config:
        return None

    # 1. Manual override
    override = _get_active_override(config)
    if override:
        return override.technician

    if not config.rotations:
        return None

    now_local = _business_local_now(business_id, db)

    if config.rotation_type == "day_of_week":
        today_dow = now_local.weekday()
        for entry in config.rotations:
            if entry.day_of_week == today_dow:
                return entry.technician

    elif config.rotation_type == "weekly_rolling":
        if not config.rolling_start_date:
            return None
        weeks_elapsed = (now_local.date() - config.rolling_start_date).days // 7
        cycle_len = len(config.rotations)
        if cycle_len == 0:
            return None
        slot = weeks_elapsed % cycle_len
        for entry in config.rotations:
            if entry.position == slot:
                return entry.technician

    return None


def _render(template: str, vars: dict) -> str:
    """Replace {{token}} placeholders in a template string."""
    def replace(m):
        return vars.get(m.group(1), m.group(0))
    return re.sub(r"\{\{(\w+)\}\}", replace, template)


def _load_dispatch_template(business_id: int, db: Session) -> str:
    """Load custom dispatch template from DB, or fall back to default."""
    from app.models.notification_template import NotificationTemplate
    saved = db.query(NotificationTemplate).filter(
        NotificationTemplate.business_id == business_id,
        NotificationTemplate.event_type == "emergency_dispatch",
        NotificationTemplate.channel == "sms",
        NotificationTemplate.is_active == True,
    ).first()
    if saved:
        return saved.body
    return DEFAULTS.get(("emergency_dispatch", "sms"), {}).get("body", DISPATCH_DEFAULT)


def _create_emergency_appointment(
    db: Session,
    business: Business,
    customer_phone: str,
    customer_name: str,
    issue_summary: str,
    tech_id: Optional[int],
    collected_address: Optional[str] = None,
) -> Optional[int]:
    """
    Create an appointment record for a dispatched emergency.

    Status is "emergency" and scheduled_start is now. NO notifications are fired
    here (confirmation/OTW/reminders) — the tech was already alerted by the
    dispatch SMS and told to contact the customer immediately. The scheduler
    jobs explicitly skip "emergency" status appointments.

    Returns the new appointment id, or None on failure.
    """
    try:
        from datetime import datetime, timezone, timedelta
        import secrets
        from app.models.service_type import ServiceType
        from app.models.customer import Customer
        from app.models.appointment import Appointment
        from app.models.contact_submission import ContactSubmission

        # 1. Dedicated "Emergency Service" type (create once per business)
        service = db.query(ServiceType).filter(
            ServiceType.business_id == business.id,
            ServiceType.name == "Emergency Service",
        ).first()
        if not service:
            service = ServiceType(
                business_id=business.id,
                name="Emergency Service",
                category="Emergency",
                description="Auto-created for emergency dispatches handled via the SMS agent.",
                duration_minutes=120,
                is_active=True,
            )
            db.add(service)
            db.flush()

        # 2. Find or create the customer by phone
        customer = db.query(Customer).filter(
            Customer.phone == customer_phone,
            Customer.business_id == business.id,
        ).first()
        if not customer:
            parts = (customer_name or "Emergency Caller").split(None, 1)
            customer = Customer(
                business_id=business.id,
                first_name=parts[0],
                last_name=parts[1] if len(parts) > 1 else "",
                phone=customer_phone,
            )
            db.add(customer)
            db.flush()

        # 3. Address - prefer what the agent collected in chat; otherwise enrich
        #    from the most recent (non-deleted) contact submission for this phone.
        address = (collected_address or "").strip() or None
        if not address:
            cs = db.query(ContactSubmission).filter(
                ContactSubmission.business_id == business.id,
                ContactSubmission.phone == customer_phone,
                ContactSubmission.deleted_at == None,
            ).order_by(ContactSubmission.id.desc()).first()
            if cs:
                addr_parts = [getattr(cs, f, None) for f in ("street_address", "city", "state", "zip_code")]
                addr_parts = [p for p in addr_parts if p]
                if addr_parts:
                    address = ", ".join(addr_parts)
        if address and not customer.address:
            customer.address = address
            db.flush()
        if not address and getattr(customer, "address", None):
            address = customer.address

        # 4. Create the appointment
        now = datetime.now(timezone.utc)
        appt = Appointment(
            business_id=business.id,
            customer_id=customer.id,
            service_type_id=service.id,
            technician_id=tech_id,
            scheduled_start=now,
            scheduled_end=now + timedelta(minutes=service.duration_minutes),
            status="emergency",
            source="emergency_sms",
            address=address,
            notes="Emergency dispatch — on-call tech alerted via SMS and instructed to contact the customer immediately.",
            problem_description=issue_summary or None,
            calendar_token=secrets.token_urlsafe(48),
        )
        db.add(appt)
        db.commit()
        logger.info(
            "oncall_notifier: emergency appointment %s created (business %s, tech %s)",
            appt.id, business.id, tech_id,
        )
        return appt.id
    except Exception as e:
        logger.error("oncall_notifier: failed to create emergency appointment: %s", e)
        db.rollback()
        return None


def dispatch_emergency(
    db: Session,
    business: Business,
    customer_phone: str,
    customer_name: str,
    issue_summary: str,
    service_address: str = "",
) -> dict:
    """
    Send an emergency dispatch SMS to the current on-call technician.

    Returns a dict describing the outcome, suitable for returning to the AI agent
    as a tool result:
      { "dispatched": True/False, "tech_name": str, "message": str }
    """
    if not settings.TWILIO_ACCOUNT_SID or not settings.TWILIO_AUTH_TOKEN:
        logger.warning("oncall_notifier: Twilio not configured — cannot dispatch")
        return {
            "dispatched": False,
            "message": "SMS dispatch unavailable — Twilio not configured.",
        }

    # Resolve on-call tech
    tech = _current_oncall_tech(business.id, db)

    # Fall back to configured fallback phone if no tech resolved
    tech_name = None
    tech_phone = None
    tech_id = None

    if tech and tech.phone:
        tech_name  = tech.name
        tech_phone = tech.phone
        tech_id    = tech.id
    else:
        # Try fallback from on-call config
        config = db.query(OnCallConfig).filter(
            OnCallConfig.business_id == business.id
        ).first()
        if config and config.fallback_phone:
            tech_phone = config.fallback_phone
            tech_name  = config.fallback_name or "On-call staff"
        else:
            logger.warning(
                "oncall_notifier: no on-call tech or fallback configured for business %s",
                business.id,
            )
            return {
                "dispatched": False,
                "message": "No on-call technician is currently configured.",
            }

    # Render the template
    template_body = _load_dispatch_template(business.id, db)
    message_body  = _render(template_body, {
        "business_name":  business.name,
        "customer_name":  customer_name or "Unknown",
        "customer_phone": customer_phone,
        "issue_summary":  issue_summary,
        "tech_name":      tech_name,
        "address":        (service_address.strip() if service_address else "") or "Not provided - please call customer",
    })

    # Send via Twilio
    from_number = business.twilio_phone_number or settings.TWILIO_PHONE_NUMBER
    if not from_number:
        return {
            "dispatched": False,
            "message": "No Twilio from-number configured for this business.",
        }

    try:
        from twilio.rest import Client
        from app.services.notifications import _normalize_phone
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        client.messages.create(
            body=message_body,
            from_=_normalize_phone(from_number),
            to=_normalize_phone(tech_phone),
        )
        logger.info(
            "oncall_notifier: dispatched emergency for business %s to %s (%s)",
            business.id, tech_name, tech_phone,
        )
        appt_id = _create_emergency_appointment(
            db, business, customer_phone, customer_name, issue_summary, tech_id,
            collected_address=service_address,
        )
        return {
            "dispatched": True,
            "tech_name":  tech_name,
            "appointment_id": appt_id,
            "message":    f"Emergency dispatched to {tech_name}. They will contact the customer shortly.",
        }
    except Exception as e:
        logger.error("oncall_notifier: Twilio send failed: %s", e)
        return {
            "dispatched": False,
            "message":    f"Failed to send dispatch SMS: {e}",
        }
