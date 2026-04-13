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

def send_sms(to_number: str, body: str, from_number: str | None = None) -> bool:
    """Send an SMS. Returns True on success, False on failure."""
    if not all([settings.TWILIO_ACCOUNT_SID,
                settings.TWILIO_AUTH_TOKEN,
                settings.TWILIO_PHONE_NUMBER]):
        logger.warning("SMS skipped — Twilio credentials not configured")
        return False

    from_num = from_number or settings.TWILIO_PHONE_NUMBER

    try:
        from twilio.rest import Client
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        client.messages.create(
            body=body,
            from_=from_num,
            to=to_number,
        )
        logger.info("SMS sent to %s from %s", to_number, from_num)
        return True
    except Exception as e:
        logger.error("SMS failed to %s: %s", to_number, e)
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


# ── High-level reminder helpers ────────────────────────────────────────────────

def _format_appointment_time(dt: datetime) -> str:
    """Return a human-friendly date/time string, e.g. 'Monday, April 7 at 10:00 AM'."""
    return dt.strftime("%A, %B %-d at %-I:%M %p")


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
