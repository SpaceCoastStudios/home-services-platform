"""
Notification service — sends SMS and email reminders, logs every attempt.

SMS:   Twilio REST API
Email: SendGrid Web API

Both channels are optional — if credentials are absent the function logs a
warning and returns without raising so the scheduler keeps running.
"""

import logging
from datetime import datetime, timezone

from app.config import settings

logger = logging.getLogger(__name__)


# ── SMS via Twilio ─────────────────────────────────────────────────────────────

def _normalize_phone(number: str) -> str:
    """
    Normalize a phone number to E.164 format for Twilio.
    Handles 10-digit US numbers (5055551234 → +15055551234),
    11-digit numbers starting with 1 (15055551234 → +15055551234),
    and numbers already in E.164 format (+15055551234 → unchanged).
    Strips spaces, dashes, dots, and parentheses before processing.
    """
    digits = "".join(c for c in number if c.isdigit())
    if number.startswith("+"):
        return number  # Already E.164 — leave as-is
    if len(digits) == 10:
        return f"+1{digits}"
    if len(digits) == 11 and digits.startswith("1"):
        return f"+{digits}"
    return number  # Unknown format — pass through and let Twilio error


def send_sms(to_number: str, body: str, from_number: str | None = None) -> bool:
    """Send an SMS. Returns True on success, False on failure."""
    if not all([settings.TWILIO_ACCOUNT_SID,
                settings.TWILIO_AUTH_TOKEN,
                settings.TWILIO_PHONE_NUMBER]):
        logger.warning("SMS skipped — Twilio credentials not configured")
        return False

    from_num = from_number or settings.TWILIO_PHONE_NUMBER
    to_e164 = _normalize_phone(to_number)

    try:
        from twilio.rest import Client
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        client.messages.create(
            body=body,
            from_=from_num,
            to=to_e164,
        )
        logger.info("SMS sent to %s from %s", to_e164, from_num)
        return True
    except Exception as e:
        logger.error("SMS failed to %s: %s", to_e164, e)
        return False


# ── Email via SendGrid ─────────────────────────────────────────────────────────

def send_email(to_email: str, subject: str, html_body: str, plain_body: str) -> bool:
    """Send an email. Returns True on success, False on failure."""
    if not settings.SENDGRID_API_KEY:
        logger.warning("Email skipped — SendGrid API key not configured")
        return False

    try:
        from sendgrid import SendGridAPIClient
        from sendgrid.helpers.mail import Mail, Content, MimeType

        message = Mail(
            from_email=(settings.sender_email, settings.sender_name),
            to_emails=to_email,
            subject=subject,
        )
        message.add_content(Content(MimeType.text, plain_body))
        message.add_content(Content(MimeType.html, html_body))

        sg = SendGridAPIClient(settings.SENDGRID_API_KEY)
        response = sg.send(message)

        if response.status_code in (200, 201, 202):
            logger.info("Email sent to %s (status %s)", to_email, response.status_code)
            return True
        else:
            logger.error("Email to %s returned status %s", to_email, response.status_code)
            return False
    except Exception as e:
        logger.error("Email failed to %s: %s", to_email, e)
        return False


# ── Escalation alert ──────────────────────────────────────────────────────────

def send_escalation_alert(db, business, alert_body: str) -> bool:
    """
    Send an SMS escalation alert to the business's on-call fallback contact.

    Used when the SMS agent escalates a conversation to human review (either via
    escalate_to_human or when emergency dispatch fires). The recipient is resolved
    in priority order:
      1. On-call config fallback_phone (already the designated emergency contact)
      2. Business.phone (main line — last resort)

    If neither is configured, logs a warning and returns False.
    """
    from app.models.oncall import OnCallConfig

    config = db.query(OnCallConfig).filter(
        OnCallConfig.business_id == business.id
    ).first()

    alert_phone = (config.fallback_phone if config and config.fallback_phone else None) or business.phone
    if not alert_phone:
        logger.warning(
            "escalation_alert: no alert phone configured for business %s — alert not sent",
            business.id,
        )
        return False

    from_number = business.twilio_phone_number or settings.TWILIO_PHONE_NUMBER
    if not from_number:
        logger.warning(
            "escalation_alert: no Twilio from-number for business %s — alert not sent",
            business.id,
        )
        return False

    sent = send_sms(alert_phone, alert_body, from_number)
    if sent:
        logger.info(
            "escalation_alert: sent to %s for business %s", alert_phone, business.id
        )
    return sent


# ── High-level reminder helpers ────────────────────────────────────────────────

def _format_appointment_time(dt: datetime) -> str:
    """Return a human-friendly date/time string, e.g. 'Monday, April 7 at 10:00 AM'."""
    return dt.strftime("%A, %B %-d at %-I:%M %p")


def send_confirmation(db, appointment) -> dict:
    """
    Send an immediate booking confirmation to the customer via SMS and/or email.
    Called right after an appointment is created.

    Returns {"sms": "sent"|"failed"|"skipped", "email": "sent"|"failed"|"skipped"}
    """
    from app.models.notification import NotificationLog
    from app.services.template_renderer import render_sms, render_email

    customer = appointment.customer
    business = appointment.business
    results = {}

    twilio_from = (business.twilio_phone_number if business else None) or settings.TWILIO_PHONE_NUMBER

    # ── SMS ────────────────────────────────────────────────────────────────────
    if customer and customer.phone:
        sms_body = render_sms("confirmation", db, business, appointment)
        sms_ok = send_sms(customer.phone, sms_body, from_number=twilio_from)
        sms_status = "sent" if sms_ok else "failed"
        results["sms"] = sms_status

        db.add(NotificationLog(
            appointment_id=appointment.id,
            type="sms",
            event="confirmation",
            sent_at=datetime.now(timezone.utc),
            status=sms_status,
        ))
    else:
        results["sms"] = "skipped"

    # ── Email ──────────────────────────────────────────────────────────────────
    if customer and customer.email:
        subject, plain, html = render_email("confirmation", db, business, appointment)
        email_ok = send_email(customer.email, subject, html, plain)
        email_status = "sent" if email_ok else "failed"
        results["email"] = email_status

        db.add(NotificationLog(
            appointment_id=appointment.id,
            type="email",
            event="confirmation",
            sent_at=datetime.now(timezone.utc),
            status=email_status,
        ))
    else:
        results["email"] = "skipped"

    db.commit()
    logger.info("Confirmation sent for appt %d — SMS: %s, Email: %s",
                appointment.id, results.get("sms"), results.get("email"))
    return results


def send_reminder(db, appointment) -> dict:
    """
    Send a 24-hour reminder for a single appointment via SMS and/or email.
    Uses per-business notification templates with fallback to defaults.

    Logs each attempt to notification_logs and returns a summary dict:
        {"sms": "sent"|"failed"|"skipped", "email": "sent"|"failed"|"skipped"}
    """
    from app.models.notification import NotificationLog
    from app.services.template_renderer import render_sms, render_email

    customer = appointment.customer
    business = appointment.business
    results = {}

    # Use business-specific Twilio number if configured
    twilio_from = (business.twilio_phone_number if business else None) or settings.TWILIO_PHONE_NUMBER

    # ── SMS ────────────────────────────────────────────────────────────────────
    if customer.phone:
        sms_body = render_sms("reminder_24h", db, business, appointment)
        sms_ok = send_sms(customer.phone, sms_body, from_number=twilio_from)
        sms_status = "sent" if sms_ok else "failed"
        results["sms"] = sms_status

        db.add(NotificationLog(
            appointment_id=appointment.id,
            type="sms",
            event="reminder_24h",
            sent_at=datetime.now(timezone.utc),
            status=sms_status,
        ))
    else:
        results["sms"] = "skipped"

    # ── Email ──────────────────────────────────────────────────────────────────
    if customer.email:
        subject, plain, html = render_email("reminder_24h", db, business, appointment)
        email_ok = send_email(customer.email, subject, html, plain)
        email_status = "sent" if email_ok else "failed"
        results["email"] = email_status

        db.add(NotificationLog(
            appointment_id=appointment.id,
            type="email",
            event="reminder_24h",
            sent_at=datetime.now(timezone.utc),
            status=email_status,
        ))
    else:
        results["email"] = "skipped"

    db.commit()
    return results


def send_review_request(db, appointment) -> dict:
    """
    Send a review request after an appointment is completed.
    Only sends if the business has a google_review_url configured.

    Returns {"sms": ..., "email": ...}
    """
    from app.models.notification import NotificationLog
    from app.services.template_renderer import render_sms, render_email

    business = appointment.business
    customer = appointment.customer
    results = {}

    # Don't send if no review URL configured
    if not business or not getattr(business, "google_review_url", None):
        return {"sms": "skipped", "email": "skipped"}

    twilio_from = (business.twilio_phone_number if business else None) or settings.TWILIO_PHONE_NUMBER

    # ── SMS ────────────────────────────────────────────────────────────────────
    if customer and customer.phone:
        sms_body = render_sms("review_request", db, business, appointment)
        sms_ok = send_sms(customer.phone, sms_body, from_number=twilio_from)
        sms_status = "sent" if sms_ok else "failed"
        results["sms"] = sms_status

        db.add(NotificationLog(
            appointment_id=appointment.id,
            type="sms",
            event="review_request",
            sent_at=datetime.now(timezone.utc),
            status=sms_status,
        ))
    else:
        results["sms"] = "skipped"

    # ── Email ──────────────────────────────────────────────────────────────────
    if customer and customer.email:
        subject, plain, html = render_email("review_request", db, business, appointment)
        email_ok = send_email(customer.email, subject, html, plain)
        email_status = "sent" if email_ok else "failed"
        results["email"] = email_status

        db.add(NotificationLog(
            appointment_id=appointment.id,
            type="email",
            event="review_request",
            sent_at=datetime.now(timezone.utc),
            status=email_status,
        ))
    else:
        results["email"] = "skipped"

    db.commit()
    logger.info("Review request sent for appt %d — %s", appointment.id, results)
    return results


def send_otw_tech_prompt(db, appointment) -> bool:
    """
    Text the assigned technician to ask them to reply YES when heading to the job.
    Returns True if the SMS was sent.
    """
    from app.models.notification import NotificationLog
    from app.services.template_renderer import render_sms_raw

    tech = appointment.technician
    business = appointment.business

    if not tech or not tech.phone:
        logger.warning("OTW tech prompt skipped — no tech phone for appt %d", appointment.id)
        return False

    twilio_from = (business.twilio_phone_number if business else None) or settings.TWILIO_PHONE_NUMBER

    body = render_sms_raw(
        "otw_tech_prompt", db, business,
        customer_name=appointment.customer.full_name if appointment.customer else "your customer",
        address=appointment.address or (appointment.customer.address if appointment.customer else "the job site"),
    )

    ok = send_sms(tech.phone, body, from_number=twilio_from)

    db.add(NotificationLog(
        appointment_id=appointment.id,
        type="sms",
        event="otw_tech_prompt",
        sent_at=datetime.now(timezone.utc),
        status="sent" if ok else "failed",
    ))
    db.commit()

    logger.info("OTW tech prompt %s → tech %s for appt %d", "sent" if ok else "failed", tech.phone, appointment.id)
    return ok


def send_otw_tech_complete_prompt(db, appointment) -> bool:
    """
    After the tech confirms they're on the way, text them:
    "Got it! Reply YES when you're finished with the job."
    Logs as event 'otw_tech_complete_prompt'.
    """
    from app.models.notification import NotificationLog
    from app.services.template_renderer import render_sms_raw

    tech = appointment.technician
    business = appointment.business

    if not tech or not tech.phone:
        return False

    twilio_from = (business.twilio_phone_number if business else None) or settings.TWILIO_PHONE_NUMBER

    body = render_sms_raw("otw_tech_complete_prompt", db, business)

    ok = send_sms(tech.phone, body, from_number=twilio_from)

    db.add(NotificationLog(
        appointment_id=appointment.id,
        type="sms",
        event="otw_tech_complete_prompt",
        sent_at=datetime.now(timezone.utc),
        status="sent" if ok else "failed",
    ))
    db.commit()

    logger.info(
        "OTW complete prompt %s → tech %s for appt %d",
        "sent" if ok else "failed", tech.phone, appointment.id,
    )
    return ok


def send_otw_customer_notification(db, appointment) -> bool:
    """
    Text the customer that their technician is on the way.
    Called when the technician replies YES to the OTW prompt.
    Returns True if the SMS was sent.
    """
    from app.models.notification import NotificationLog
    from app.services.template_renderer import render_sms_raw

    customer = appointment.customer
    business = appointment.business

    if not customer or not customer.phone:
        logger.warning("OTW customer notification skipped — no customer phone for appt %d", appointment.id)
        return False

    twilio_from = (business.twilio_phone_number if business else None) or settings.TWILIO_PHONE_NUMBER

    body = render_sms_raw(
        "otw_customer", db, business,
        customer_name=customer.first_name or "there",
        business_name=business.name if business else "us",
    )

    ok = send_sms(customer.phone, body, from_number=twilio_from)

    db.add(NotificationLog(
        appointment_id=appointment.id,
        type="sms",
        event="otw_customer",
        sent_at=datetime.now(timezone.utc),
        status="sent" if ok else "failed",
    ))
    db.commit()

    logger.info("OTW customer notification %s → %s for appt %d", "sent" if ok else "failed", customer.phone, appointment.id)
    return ok


def _build_kickoff_body(tech, all_appts: list, schedule_url: str | None) -> str:
    """
    Build the morning kickoff SMS body showing all of today's appointments.

    Format:
      Good morning [Name]! You have X jobs today:

      1. 9:00 AM – AC Repair
         John Smith · 123 Main St
         Problem: Compressor not running…

      Full details:
      https://...

      Reply YES when heading to stop 1.
    """
    from zoneinfo import ZoneInfo
    from datetime import timezone as _tz

    appt_count = len(all_appts)
    tech_first = tech.name.split()[0] if tech.name else "there"

    # Determine business timezone for time formatting
    business = all_appts[0].business if all_appts else None
    tz_str = getattr(business, "timezone", "America/New_York") or "America/New_York"
    try:
        tz = ZoneInfo(tz_str)
    except Exception:
        tz = ZoneInfo("America/New_York")

    lines = [f"Good morning {tech_first}! You have {appt_count} job{'s' if appt_count != 1 else ''} today:"]

    for i, appt in enumerate(all_appts, start=1):
        local_dt = appt.scheduled_start.replace(tzinfo=_tz.utc).astimezone(tz)
        time_str = local_dt.strftime("%-I:%M %p")

        customer = appt.customer
        cust_name = customer.full_name if customer else "Customer"

        service = appt.service_type
        svc_name = service.name if service else "Service"

        address = appt.address or (
            getattr(customer, "address", "") if customer else ""
        ) or ""
        short_addr = address.split(",")[0].strip() if address else ""

        problem = appt.problem_description or ""
        if problem and len(problem) > 52:
            problem = problem[:50].rstrip() + "…"

        entry_lines = [f"\n{i}. {time_str} – {svc_name}"]
        detail = " · ".join(filter(None, [cust_name, short_addr]))
        if detail:
            entry_lines.append(f"   {detail}")
        if problem:
            entry_lines.append(f"   Problem: {problem}")

        lines.append("\n".join(entry_lines))

    if schedule_url:
        lines.append(f"\nFull details:\n{schedule_url}")

    lines.append("\nReply YES when heading to stop 1.")

    return "\n".join(lines)


def send_otw_morning_kickoff(
    db, first_appt, tech, all_appts: list, schedule_url: str | None = None
) -> bool:
    """
    Send the morning kickoff SMS to a technician ~2 hours before their first appointment.
    Shows a numbered summary of ALL of today's appointments with service, customer first
    name, address, and problem description (truncated to ~50 chars).
    Includes a link to the tech's public no-login schedule page.
    Prompts tech to reply YES when heading to stop 1.

    Idempotency is handled by the caller checking notification_logs before calling.
    """
    from app.models.notification import NotificationLog

    business = first_appt.business

    if not tech or not tech.phone:
        logger.warning("Morning kickoff skipped — no tech phone for appt %d", first_appt.id)
        return False

    twilio_from = (business.twilio_phone_number if business else None) or settings.TWILIO_PHONE_NUMBER
    body = _build_kickoff_body(tech, all_appts, schedule_url)

    ok = send_sms(tech.phone, body, from_number=twilio_from)

    db.add(NotificationLog(
        appointment_id=first_appt.id,
        technician_id=tech.id,
        type="sms",
        event="otw_morning_kickoff",
        sent_at=datetime.now(timezone.utc),
        status="sent" if ok else "failed",
    ))
    db.commit()

    logger.info(
        "Morning kickoff %s → tech %s (%d jobs) for appt %d",
        "sent" if ok else "failed", tech.phone, len(all_appts), first_appt.id,
    )
    return ok


def send_otw_morning_no_appointments(db, tech, business) -> bool:
    """
    Send "no appointments today" morning message to a technician.
    Logged against technician_id only (appointment_id = NULL).
    Fired once between 07:00–08:00 local business time.
    """
    from app.models.notification import NotificationLog

    if not tech or not tech.phone:
        return False

    twilio_from = (business.twilio_phone_number if business else None) or settings.TWILIO_PHONE_NUMBER

    tech_first = tech.name.split()[0] if tech.name else "there"
    body = (
        f"Good morning {tech_first}! No appointments scheduled for you today. "
        f"Enjoy your day off! \U0001f334"
    )

    ok = send_sms(tech.phone, body, from_number=twilio_from)

    db.add(NotificationLog(
        appointment_id=None,
        technician_id=tech.id,
        type="sms",
        event="otw_morning_kickoff",
        sent_at=datetime.now(timezone.utc),
        status="sent" if ok else "failed",
    ))
    db.commit()

    logger.info(
        "No-appointments morning message %s → tech %s",
        "sent" if ok else "failed", tech.phone,
    )
    return ok


def send_otw_next_stop(db, appointment, tech) -> bool:
    """
    Send a "Great work! Ready for your next stop?" prompt between jobs.
    Called by _send_next_otw_if_due() after the tech marks a job complete
    and there are more appointments remaining today.
    """
    from app.models.notification import NotificationLog
    from app.services.template_renderer import render_sms_raw

    business = appointment.business

    if not tech or not tech.phone:
        logger.warning("Next stop prompt skipped — no tech phone for appt %d", appointment.id)
        return False

    twilio_from = (business.twilio_phone_number if business else None) or settings.TWILIO_PHONE_NUMBER

    body = render_sms_raw(
        "otw_next_stop", db, business,
        customer_name=appointment.customer.full_name if appointment.customer else "your customer",
        address=appointment.address or (appointment.customer.address if appointment.customer else "the job site"),
    )

    ok = send_sms(tech.phone, body, from_number=twilio_from)

    db.add(NotificationLog(
        appointment_id=appointment.id,
        type="sms",
        event="otw_next_stop",
        sent_at=datetime.now(timezone.utc),
        status="sent" if ok else "failed",
    ))
    db.commit()

    logger.info(
        "Next stop prompt %s → tech %s for appt %d",
        "sent" if ok else "failed", tech.phone, appointment.id,
    )
    return ok


def send_otw_day_complete(db, tech, business, last_appointment) -> bool:
    """
    Send "That's a wrap!" after the technician completes their last job of the day.
    Called by _send_next_otw_if_due() when no more appointments remain today.
    """
    from app.models.notification import NotificationLog
    from app.services.template_renderer import render_sms_raw

    if not tech or not tech.phone:
        logger.warning("Day complete message skipped — no tech phone")
        return False

    twilio_from = (business.twilio_phone_number if business else None) or settings.TWILIO_PHONE_NUMBER

    body = render_sms_raw(
        "otw_day_complete", db, business,
        tech_name=tech.name.split()[0] if tech.name else "there",
    )

    ok = send_sms(tech.phone, body, from_number=twilio_from)

    db.add(NotificationLog(
        appointment_id=last_appointment.id,
        type="sms",
        event="otw_day_complete",
        sent_at=datetime.now(timezone.utc),
        status="sent" if ok else "failed",
    ))
    db.commit()

    logger.info(
        "Day complete message %s → tech %s",
        "sent" if ok else "failed", tech.phone,
    )
    return ok
