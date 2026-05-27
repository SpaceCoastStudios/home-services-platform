"""
Template renderer — loads a notification template for a business and renders tokens.

Usage:
    text = render("confirmation", "sms", db, business, appointment)
    subject, body = render_email("confirmation", db, business, appointment)
"""

import re
import logging
import pytz
from datetime import datetime

from sqlalchemy.orm import Session

from app.models.appointment import Appointment
from app.models.business import Business
from app.models.notification_template import NotificationTemplate, DEFAULTS
from app.utils.ics_generator import get_all_calendar_links

logger = logging.getLogger(__name__)


def _load_template(
    db: Session, business_id: int, event_type: str, channel: str
) -> tuple[str | None, str]:
    """
    Return (subject, body) for the given event/channel.
    Tries business-specific saved template first, falls back to default constants.
    """
    saved = (
        db.query(NotificationTemplate)
        .filter(
            NotificationTemplate.business_id == business_id,
            NotificationTemplate.event_type == event_type,
            NotificationTemplate.channel == channel,
            NotificationTemplate.is_active == True,
        )
        .first()
    )
    if saved:
        return saved.subject, saved.body

    default = DEFAULTS.get((event_type, channel), {})
    return default.get("subject"), default.get("body", "")


def _build_vars(business: Business, appointment: Appointment) -> dict:
    """Build the token substitution dict from an appointment."""
    customer = appointment.customer
    service = appointment.service_type
    tech = appointment.technician

    # Format date/time in the business's local timezone (stored as UTC in DB)
    dt = appointment.scheduled_start
    biz_tz_str = getattr(business, "timezone", None) or "America/New_York"
    try:
        biz_tz = pytz.timezone(biz_tz_str)
    except Exception:
        biz_tz = pytz.utc
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=pytz.utc)
    dt_local = dt.astimezone(biz_tz)
    try:
        date_time_str = dt_local.strftime("%A, %B %-d at %-I:%M %p")
    except ValueError:
        # Windows doesn't support %-d / %-I
        date_time_str = dt_local.strftime("%A, %B %d at %I:%M %p").replace(" 0", " ")

    # Calendar links
    try:
        cal_links = get_all_calendar_links(appointment.calendar_token)
    except Exception:
        cal_links = {}
    calendar_link = cal_links.get("landing_page", "")

    return {
        "customer_name": customer.first_name if customer else "there",
        "business_name": business.name or "",
        "service_name": service.name if service else "appointment",
        "date_time": date_time_str,
        "technician_name": tech.name if tech else "a technician",
        "address": appointment.address or (customer.address if customer and hasattr(customer, "address") else "") or "",
        "calendar_link": calendar_link,
        "cal_links": cal_links,
        "business_phone": business.phone or "",
    }


def _render(template_body: str, vars: dict) -> str:
    """Replace {{token}} placeholders with values."""
    def replacer(match):
        key = match.group(1).strip()
        return str(vars.get(key, match.group(0)))
    return re.sub(r"\{\{(\w+)\}\}", replacer, template_body)


def render_sms(event_type: str, db: Session, business: Business, appointment: Appointment) -> str:
    """Render the SMS body for a given event type."""
    _, body = _load_template(db, business.id, event_type, "sms")
    vars = _build_vars(business, appointment)
    # Inject review link if the business has one configured
    if hasattr(business, "google_review_url") and business.google_review_url:
        vars["review_link"] = business.google_review_url
    return _render(body, vars)


def render_sms_raw(event_type: str, db: Session, business: Business, **kwargs) -> str:
    """
    Render an SMS template with an arbitrary token dict instead of a full
    Appointment object.  Used for OTW prompts and other non-appointment messages.
    """
    _, body = _load_template(db, business.id, event_type, "sms")
    vars = {
        "business_name": business.name or "",
        "business_phone": business.phone or "",
        **kwargs,
    }
    return _render(body, vars)


def render_email(
    event_type: str, db: Session, business: Business, appointment: Appointment
) -> tuple[str, str, str]:
    """
    Render email for a given event type.
    Returns (subject, plain_text_body, html_body).
    """
    subject_tpl, body_tpl = _load_template(db, business.id, event_type, "email")
    vars = _build_vars(business, appointment)
    # Inject review link if the business has one configured
    if hasattr(business, "google_review_url") and business.google_review_url:
        vars["review_link"] = business.google_review_url

    subject = _render(subject_tpl or "", vars)
    plain = _render(body_tpl or "", vars)
    html = _build_html_email(plain, subject, business, vars.get("cal_links"))

    return subject, plain, html


def _build_html_email(plain_body: str, title: str, business: Business, cal_links: dict | None = None) -> str:
    """Wrap plain text email body in a branded HTML envelope."""
    brand_color = business.brand_color or "#2563eb"
    business_name = business.name or "Space Coast Studios"

    # Convert plain text paragraphs to HTML
    paragraphs = [p.strip() for p in plain_body.split("\n\n") if p.strip()]
    body_html = ""
    for para in paragraphs:
        # Skip the "Use the calendar buttons below" line — we render real buttons instead
        if "calendar buttons below" in para.lower():
            continue
        lines = para.replace("\n", "<br>")
        body_html += f'<p style="margin:0 0 14px 0;">{lines}</p>\n'

    # Calendar buttons
    cal_html = ""
    if cal_links:
        btn_style = (
            f"display:inline-block;margin:4px;padding:10px 18px;border-radius:6px;"
            f"background:{brand_color};color:white;text-decoration:none;"
            f"font-size:13px;font-weight:600;"
        )
        ghost_style = (
            f"display:inline-block;margin:4px;padding:10px 18px;border-radius:6px;"
            f"border:1px solid {brand_color};color:{brand_color};text-decoration:none;"
            f"font-size:13px;font-weight:600;"
        )
        cal_html = f"""
        <div style="margin:20px 0;padding:20px;background:#f8fafc;border-radius:8px;text-align:center;">
          <p style="margin:0 0 14px;font-size:14px;font-weight:600;color:#374151;">Add to your calendar</p>
          <div>
            <a href="{cal_links.get('google','')}" target="_blank" style="{btn_style}">Google Calendar</a>
            <a href="{cal_links.get('ical','')}" target="_blank" style="{ghost_style}">Apple / iCal</a>
            <a href="{cal_links.get('outlook','')}" target="_blank" style="{ghost_style}">Outlook</a>
            <a href="{cal_links.get('yahoo','')}" target="_blank" style="{ghost_style}">Yahoo</a>
          </div>
        </div>"""

    contact_line = ""
    if business.phone:
        contact_line += f'<a href="tel:{business.phone}" style="color:{brand_color};">{business.phone}</a>'
    if business.email:
        sep = " &nbsp;|&nbsp; " if contact_line else ""
        contact_line += f'{sep}<a href="mailto:{business.email}" style="color:{brand_color};">{business.email}</a>'

    return f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#f3f4f6;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Arial,sans-serif;">
  <div style="max-width:600px;margin:32px auto;">
    <div style="background:{brand_color};color:white;padding:24px 28px;border-radius:8px 8px 0 0;">
      <h1 style="margin:0;font-size:18px;font-weight:700;">{business_name}</h1>
    </div>
    <div style="background:white;padding:28px;border:1px solid #e5e7eb;border-top:none;color:#374151;font-size:15px;line-height:1.6;">
      {body_html}
      {cal_html}
    </div>
    <div style="background:#f9fafb;padding:16px 28px;border:1px solid #e5e7eb;border-top:none;border-radius:0 0 8px 8px;text-align:center;">
      <p style="margin:0;font-size:12px;color:#9ca3af;">{contact_line}</p>
      <p style="margin:8px 0 0;font-size:11px;color:#d1d5db;">Reply STOP to opt out of SMS messages. Msg &amp; data rates may apply.</p>
    </div>
  </div>
</body>
</html>"""
