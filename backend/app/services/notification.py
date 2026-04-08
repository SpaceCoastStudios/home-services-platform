"""Notification service — SMS + email dispatch with calendar links."""

import logging
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.config import settings
from app.models.appointment import Appointment
from app.models.notification import NotificationLog
from app.utils.ics_generator import get_all_calendar_links

logger = logging.getLogger(__name__)


def _send_sms(to: str, message: str, from_number: str | None = None) -> bool:
    """Send an SMS via Twilio. Returns True on success."""
    if not settings.TWILIO_ACCOUNT_SID:
        logger.warning("Twilio not configured — skipping SMS to %s", to)
        logger.info("SMS content: %s", message)
        return False

    try:
        from twilio.rest import Client
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        client.messages.create(
            body=message,
            from_=from_number or settings.TWILIO_PHONE_NUMBER,
            to=to,
        )
        return True
    except Exception as e:
        logger.error("Failed to send SMS to %s: %s", to, e)
        return False


def _send_email(to: str, subject: str, html_body: str) -> bool:
    """Send an email via SendGrid. Returns True on success."""
    if not settings.SENDGRID_API_KEY:
        logger.warning("SendGrid not configured — skipping email to %s", to)
        logger.info("Email subject: %s", subject)
        return False

    try:
        import sendgrid
        from sendgrid.helpers.mail import Mail, Email, To, Content

        sg = sendgrid.SendGridAPIClient(api_key=settings.SENDGRID_API_KEY)
        mail = Mail(
            from_email=Email(settings.sender_email, settings.sender_name),
            to_emails=To(to),
            subject=subject,
            html_content=Content("text/html", html_body),
        )
        sg.client.mail.send.post(request_body=mail.get())
        return True
    except Exception as e:
        logger.error("Failed to send email to %s: %s", to, e)
        return False


def send_appointment_confirmation(db: Session, appointment: Appointment):
    """Send confirmation SMS + email using per-business templates."""
    from app.services.template_renderer import render_sms, render_email

    customer = appointment.customer
    business = appointment.business

    # Use business-specific Twilio number if configured
    twilio_from = (business.twilio_phone_number if business else None) or settings.TWILIO_PHONE_NUMBER

    # SMS
    if customer.phone:
        sms_text = render_sms("confirmation", db, business, appointment)
        sms_ok = _send_sms(customer.phone, sms_text, from_number=twilio_from)
        _log_notification(db, appointment.id, "sms", "confirmation", sms_ok)

    # Email
    if customer.email:
        subject, plain, html = render_email("confirmation", db, business, appointment)
        email_ok = _send_email(customer.email, subject, html)
        _log_notification(db, appointment.id, "email", "confirmation", email_ok)

    appointment.calendar_links_sent = True
    db.commit()


def _build_confirmation_email(appointment: Appointment, cal_links: dict) -> str:
    """Build HTML confirmation email with calendar buttons."""
    service_name = appointment.service_type.name if appointment.service_type else "Appointment"
    tech_name = appointment.technician.name if appointment.technician else "TBD"
    date_str = appointment.scheduled_start.strftime("%A, %B %d, %Y")
    time_str = f"{appointment.scheduled_start.strftime('%I:%M %p')} - {appointment.scheduled_end.strftime('%I:%M %p')}"
    location = appointment.address or (appointment.customer.address if appointment.customer else "")

    return f"""
    <div style="font-family: -apple-system, sans-serif; max-width: 600px; margin: 0 auto;">
        <div style="background: #2563eb; color: white; padding: 24px; text-align: center; border-radius: 8px 8px 0 0;">
            <h1 style="margin: 0; font-size: 22px;">Appointment Confirmed</h1>
        </div>
        <div style="background: white; padding: 24px; border: 1px solid #e5e7eb;">
            <p>Hi {appointment.customer.first_name},</p>
            <p>Your <strong>{service_name}</strong> appointment has been confirmed.</p>

            <div style="background: #f9fafb; border-radius: 8px; padding: 16px; margin: 16px 0;">
                <p><strong>Date:</strong> {date_str}</p>
                <p><strong>Time:</strong> {time_str}</p>
                <p><strong>Technician:</strong> {tech_name}</p>
                <p><strong>Location:</strong> {location or 'TBD'}</p>
            </div>

            <p style="font-weight: 600; margin-top: 20px;">Add to Your Calendar:</p>
            <div style="display: flex; gap: 8px; flex-wrap: wrap; margin-top: 8px;">
                <a href="{cal_links['google']}" style="background: #4285f4; color: white; padding: 10px 16px; border-radius: 6px; text-decoration: none; font-size: 14px;">Google Calendar</a>
                <a href="{cal_links['ical']}" style="background: #333; color: white; padding: 10px 16px; border-radius: 6px; text-decoration: none; font-size: 14px;">Apple Calendar</a>
                <a href="{cal_links['outlook']}" style="background: #0078d4; color: white; padding: 10px 16px; border-radius: 6px; text-decoration: none; font-size: 14px;">Outlook</a>
                <a href="{cal_links['yahoo']}" style="background: #6001d2; color: white; padding: 10px 16px; border-radius: 6px; text-decoration: none; font-size: 14px;">Yahoo</a>
            </div>
        </div>
        <div style="text-align: center; padding: 16px; color: #6b7280; font-size: 12px;">
            <p>Questions? Call us or reply to this email.</p>
        </div>
    </div>
    """


def _log_notification(db: Session, appointment_id: int, ntype: str, event: str, success: bool):
    log = NotificationLog(
        appointment_id=appointment_id,
        type=ntype,
        event=event,
        status="sent" if success else "failed",
    )
    db.add(log)
    db.commit()
