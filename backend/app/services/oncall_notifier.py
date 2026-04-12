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
    "Issue: {{issue_summary}}\n\n"
    "Respond immediately."
)


def _get_active_override(config: OnCallConfig) -> Optional[OnCallOverride]:
    now = datetime.now(timezone.utc)
    for override in config.overrides:
        if override.expires_at > now:
            return override
    return None


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

    now_utc = datetime.now(timezone.utc)

    if config.rotation_type == "day_of_week":
        today_dow = now_utc.weekday()
        for entry in config.rotations:
            if entry.day_of_week == today_dow:
                return entry.technician

    elif config.rotation_type == "weekly_rolling":
        if not config.rolling_start_date:
            return None
        ref = datetime(
            config.rolling_start_date.year,
            config.rolling_start_date.month,
            config.rolling_start_date.day,
            tzinfo=timezone.utc,
        )
        weeks_elapsed = (now_utc - ref).days // 7
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


def dispatch_emergency(
    db: Session,
    business: Business,
    customer_phone: str,
    customer_name: str,
    issue_summary: str,
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

    if tech and tech.phone:
        tech_name  = tech.name
        tech_phone = tech.phone
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
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        client.messages.create(body=message_body, from_=from_number, to=tech_phone)
        logger.info(
            "oncall_notifier: dispatched emergency for business %s to %s (%s)",
            business.id, tech_name, tech_phone,
        )
        return {
            "dispatched": True,
            "tech_name":  tech_name,
            "message":    f"Emergency dispatched to {tech_name}. They will contact the customer shortly.",
        }
    except Exception as e:
        logger.error("oncall_notifier: Twilio send failed: %s", e)
        return {
            "dispatched": False,
            "message":    f"Failed to send dispatch SMS: {e}",
        }
