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

def send_sms(to_number: str, body: str) -> bool:
    """Send an SMS. Returns True on success, False on failure."""
    if not all([settings.TWILIO_ACCOUNT_SID,
                settings.TWILIO_AUTH_TOKEN,
                settings.TWILIO_PHONE_NUMBER]):
        logger.warning("SMS skipped — Twilio credentials not configured")
        return False

    try:
        from twilio.rest import Client
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        client.messages.create(
            body=body,
            from_=settings.TWILIO_PHONE_NUMBER,
            to=to_number,
        )
        logger.info("SMS sent to %s", to_number)
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

    Logs each attempt to notification_logs and returns a summary dict:
        {"sms": "sent"|"failed"|"skipped", "email": "sent"|"failed"|"skipped"}
    """
    from app.models.notification import NotificationLog

    customer = appointment.customer
    business = appointment.business
    service  = appointment.service_type

    appt_time_str = _format_appointment_time(appointment.scheduled_start)

    results = {}

    # ── SMS ────────────────────────────────────────────────────────────────────
    if customer.phone:
        sms_body = (
            f"Reminder: Your {service.name} appointment with {business.name} "
            f"is scheduled for {appt_time_str}. "
            f"Reply STOP to opt out."
        )
        sms_ok = send_sms(customer.phone, sms_body)
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
        subject = f"Appointment reminder — {appt_time_str}"

        plain = (
            f"Hi {customer.first_name},\n\n"
            f"This is a reminder that your {service.name} appointment with "
            f"{business.name} is scheduled for {appt_time_str}.\n\n"
            f"If you need to reschedule or have questions, please reply to this "
            f"email or call us.\n\n"
            f"Thank you,\n{business.name}"
        )

        html = f"""
        <div style="font-family:Arial,sans-serif;max-width:560px;margin:0 auto;color:#1e293b;">
          <div style="background:#f97316;padding:24px 32px;border-radius:8px 8px 0 0;">
            <h2 style="margin:0;color:#ffffff;font-size:1.3rem;">Appointment Reminder</h2>
          </div>
          <div style="padding:32px;border:1px solid #e2e8f0;border-top:none;border-radius:0 0 8px 8px;">
            <p style="margin:0 0 16px;">Hi {customer.first_name},</p>
            <p style="margin:0 0 16px;">
              This is a friendly reminder about your upcoming appointment:
            </p>
            <div style="background:#f8fafc;border-left:4px solid #f97316;
                        padding:16px 20px;border-radius:4px;margin:0 0 24px;">
              <strong style="font-size:1.1rem;">{service.name}</strong><br>
              <span style="color:#64748b;font-size:0.95rem;">{appt_time_str}</span><br>
              <span style="color:#64748b;font-size:0.95rem;">{business.name}</span>
              {"<br><span style='color:#64748b;font-size:0.95rem;'>" + appointment.address + "</span>" if appointment.address else ""}
            </div>
            <p style="margin:0 0 16px;font-size:0.9rem;color:#64748b;">
              Need to reschedule or have questions? Reply to this email or give us a call.
            </p>
            <p style="margin:0;font-size:0.9rem;">
              Thank you,<br><strong>{business.name}</strong>
            </p>
          </div>
        </div>
        """

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
