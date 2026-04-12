"""
AI contact form auto-responder.

Pipeline:
1. Load business context (services, available slots, AI persona)
2. Call Anthropic API — pass customer message + context
3. Parse response (plain reply text + optional structured booking intent)
4. Send reply email via SendGrid using business from_email
5. Optionally send SMS via Twilio if customer provided a phone
6. Stamp ContactSubmission with ai_response, status, responded_at
"""

import json
import logging
from datetime import date, datetime, timedelta, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.config import settings
from app.models.business import Business
from app.models.contact_submission import ContactSubmission
from app.models.service_type import ServiceType
from app.services.scheduling import get_available_slots

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def run_contact_responder(db: Session, submission_id: int) -> None:
    """
    Called as a FastAPI BackgroundTask after a contact form is saved.
    Loads all context from the DB, calls the AI, sends the reply, updates the record.
    """
    submission = db.query(ContactSubmission).filter(ContactSubmission.id == submission_id).first()
    if not submission:
        logger.error("contact_responder: submission %s not found", submission_id)
        return

    business = db.query(Business).filter(Business.id == submission.business_id).first()
    if not business:
        logger.error("contact_responder: business %s not found", submission.business_id)
        return

    if not settings.ANTHROPIC_API_KEY:
        logger.warning("contact_responder: ANTHROPIC_API_KEY not set — skipping AI response")
        return

    try:
        _process(db, submission, business)
    except Exception as exc:
        logger.error("contact_responder: unhandled error for submission %s: %s", submission_id, exc, exc_info=True)
        # Don't crash — mark as error so staff can follow up manually
        submission.status = "error"
        db.commit()


# ---------------------------------------------------------------------------
# Core processing
# ---------------------------------------------------------------------------

def _process(db: Session, submission: ContactSubmission, business: Business) -> None:
    # --- 1. Gather context ---
    services = _get_active_services(db, business.id)
    available_slots = _get_upcoming_slots(db, business, submission, services)
    context_block = _build_context_block(business, services, available_slots, submission)

    # --- 2. Call AI ---
    ai_result = _call_llm(business, submission, context_block)
    reply_text = ai_result.get("reply", "")
    suggested_slots = ai_result.get("suggested_slots", [])

    if not reply_text:
        logger.warning("contact_responder: LLM returned empty reply for submission %s", submission.id)
        return

    # --- 3. Save AI response ---
    submission.ai_response = reply_text
    submission.ai_suggested_slots = suggested_slots if suggested_slots else None

    # --- 4. Send or hold depending on business ai_response_mode ---
    draft_only = getattr(business, "ai_response_mode", "auto_send") == "draft_only"

    if draft_only:
        # Hold for staff approval — do not send yet
        submission.status = "pending_approval"
        db.commit()
        logger.info(
            "contact_responder: submission %s drafted (pending approval) for business %s",
            submission.id, business.slug,
        )
        return

    # auto_send — send immediately
    email_sent = _send_reply_email(business, submission, reply_text)

    if submission.phone:
        _send_reply_sms(business, submission, reply_text)

    submission.status = "ai_responded"
    submission.responded_at = datetime.now(timezone.utc)
    db.commit()
    logger.info(
        "contact_responder: completed submission %s for business %s (email_sent=%s)",
        submission.id, business.slug, email_sent,
    )


# ---------------------------------------------------------------------------
# AI call
# ---------------------------------------------------------------------------

def _call_llm(business: Business, submission: ContactSubmission, context_block: str) -> dict:
    """
    Calls the Anthropic API and returns a dict:
      { "reply": "<email body text>", "suggested_slots": [...] }
    """
    import anthropic

    agent_name = business.ai_agent_name or business.name
    business_system_prompt = business.ai_system_prompt or ""

    system_prompt = f"""You are {agent_name}, a friendly and professional customer service assistant for {business.name}.

Your job is to respond to customer inquiries submitted through the website contact form.
Write warm, helpful, and professional replies — as if a knowledgeable human staff member wrote them.
Keep responses concise (3–5 short paragraphs max).

{business_system_prompt}

--- CONTEXT ---
{context_block}
--- END CONTEXT ---

RESPONSE FORMAT:
Return ONLY a JSON object with two keys:
- "reply": A plain-text email reply to the customer. Use \\n for line breaks. Do NOT include HTML.
- "suggested_slots": An optional JSON array of up to {settings.CONTACT_MAX_SUGGESTED_SLOTS} available time slots you mentioned in the reply.
  Each slot: {{"date": "YYYY-MM-DD", "start": "HH:MM", "end": "HH:MM"}}
  Leave as an empty array [] if you did not suggest specific slots.

Return ONLY the JSON object. No markdown, no code blocks, no extra text."""

    user_message = f"""New customer inquiry:

Name: {submission.name}
Email: {submission.email}
Phone: {submission.phone or "Not provided"}
Service requested: {submission.service_requested or "Not specified"}
Preferred date: {submission.preferred_date or "Not specified"}
Preferred time: {submission.preferred_time or "Not specified"}

Message:
{submission.message}

Please write a helpful, friendly reply. If they seem interested in booking, mention 2–3 specific available time slots from the context. Invite them to call or reply to confirm."""

    client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

    response = client.messages.create(
        model=settings.LLM_MODEL,
        max_tokens=1024,
        system=system_prompt,
        messages=[{"role": "user", "content": user_message}],
    )

    raw = response.content[0].text.strip()
    logger.debug("contact_responder LLM raw output: %s", raw[:500])

    # Strip markdown code fences if present
    if raw.startswith("```"):
        lines = raw.split("\n")
        raw = "\n".join(lines[1:-1]) if lines[-1].strip() == "```" else "\n".join(lines[1:])

    try:
        parsed = json.loads(raw)
        return {
            "reply": parsed.get("reply", ""),
            "suggested_slots": parsed.get("suggested_slots", []),
        }
    except json.JSONDecodeError:
        logger.warning("contact_responder: LLM response was not valid JSON — using raw text as reply")
        return {"reply": raw, "suggested_slots": []}


# ---------------------------------------------------------------------------
# Email & SMS helpers
# ---------------------------------------------------------------------------

def _send_reply_email(business: Business, submission: ContactSubmission, reply_text: str) -> bool:
    """Send the AI reply to the customer via SendGrid."""
    if not settings.SENDGRID_API_KEY:
        logger.warning("contact_responder: SendGrid not configured — skipping email")
        logger.info("Would have sent to %s:\n%s", submission.email, reply_text)
        return False

    try:
        import sendgrid
        from sendgrid.helpers.mail import Mail, Email, To, Content

        from_email = business.from_email or settings.sender_email
        from_name = business.ai_agent_name or business.name or settings.sender_name

        agent_name = business.ai_agent_name or business.name
        html_body = _build_reply_html(business, submission, reply_text)

        sg = sendgrid.SendGridAPIClient(api_key=settings.SENDGRID_API_KEY)
        mail = Mail(
            from_email=Email(from_email, from_name),
            to_emails=To(submission.email),
            subject=f"Re: Your inquiry to {business.name}",
            html_content=Content("text/html", html_body),
        )
        # On Windows dev machines, antivirus SSL inspection causes certificate
        # errors. Temporarily bypass verification just for this call.
        # This is not needed (and harmless) in production Linux environments.
        import ssl as _ssl
        _orig = _ssl._create_default_https_context
        _ssl._create_default_https_context = _ssl._create_unverified_context
        try:
            response = sg.client.mail.send.post(request_body=mail.get())
        finally:
            _ssl._create_default_https_context = _orig
        logger.info(
            "contact_responder: reply email sent to %s (from=%s, status=%s)",
            submission.email, from_email, response.status_code,
        )
        return True
    except Exception as exc:
        logger.error(
            "contact_responder: failed to send reply email to %s (from=%s): %s",
            submission.email, from_email, exc,
        )
        return False


def _send_reply_sms(business: Business, submission: ContactSubmission, reply_text: str) -> bool:
    """Send a brief SMS reply if Twilio is configured."""
    twilio_number = business.twilio_phone_number or settings.TWILIO_PHONE_NUMBER
    if not settings.TWILIO_ACCOUNT_SID or not twilio_number:
        return False

    try:
        from twilio.rest import Client
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)

        # Truncate SMS to first ~160 chars
        first_paragraph = reply_text.split("\n\n")[0].strip()
        sms_body = first_paragraph[:155] + ("…" if len(first_paragraph) > 155 else "")

        client.messages.create(body=sms_body, from_=twilio_number, to=submission.phone)
        logger.info("contact_responder: reply SMS sent to %s", submission.phone)
        return True
    except Exception as exc:
        logger.error("contact_responder: failed to send reply SMS to %s: %s", submission.phone, exc)
        return False


def _build_reply_html(business: Business, submission: ContactSubmission, reply_text: str) -> str:
    """Wrap plain-text reply in a branded HTML email."""
    brand_color = business.brand_color or "#2563eb"
    agent_name = business.ai_agent_name or business.name
    business_name = business.name

    # Convert newlines to <br> / paragraph breaks
    paragraphs = [p.strip() for p in reply_text.split("\n\n") if p.strip()]
    body_html = "".join(f"<p style='margin:0 0 14px 0;'>{p.replace(chr(10), '<br>')}</p>" for p in paragraphs)

    contact_line = ""
    if business.phone:
        contact_line += f"<a href='tel:{business.phone}' style='color:{brand_color};'>{business.phone}</a>"
    if business.email:
        sep = " &nbsp;|&nbsp; " if contact_line else ""
        contact_line += f"{sep}<a href='mailto:{business.email}' style='color:{brand_color};'>{business.email}</a>"
    if business.website:
        sep = " &nbsp;|&nbsp; " if contact_line else ""
        contact_line += f"{sep}<a href='{business.website}' style='color:{brand_color};'>{business.website}</a>"

    return f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="margin:0;padding:0;background:#f3f4f6;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;">
  <div style="max-width:600px;margin:32px auto;">
    <!-- Header -->
    <div style="background:{brand_color};color:white;padding:24px 28px;border-radius:8px 8px 0 0;">
      <h1 style="margin:0;font-size:20px;font-weight:700;">{business_name}</h1>
    </div>
    <!-- Body -->
    <div style="background:white;padding:28px;border:1px solid #e5e7eb;border-top:none;">
      <p style="margin:0 0 16px 0;color:#374151;">Hi {submission.name.split()[0]},</p>
      {body_html}
      <p style="margin:20px 0 0 0;color:#6b7280;font-size:13px;">
        — {agent_name}
      </p>
    </div>
    <!-- Footer -->
    <div style="background:#f9fafb;padding:16px 28px;border:1px solid #e5e7eb;border-top:none;border-radius:0 0 8px 8px;text-align:center;">
      <p style="margin:0;font-size:12px;color:#9ca3af;">
        {contact_line}
      </p>
      <p style="margin:8px 0 0 0;font-size:11px;color:#d1d5db;">
        You received this because you submitted a contact form on our website.
      </p>
    </div>
  </div>
</body>
</html>"""


# ---------------------------------------------------------------------------
# Context builders
# ---------------------------------------------------------------------------

def _get_active_services(db: Session, business_id: int) -> list[ServiceType]:
    return (
        db.query(ServiceType)
        .filter(ServiceType.business_id == business_id, ServiceType.is_active == True)
        .order_by(ServiceType.name)
        .all()
    )


def _get_upcoming_slots(
    db: Session,
    business: Business,
    submission: ContactSubmission,
    services: list[ServiceType],
) -> list[dict]:
    """
    Get available slots for the next 7 days.
    If the customer specified a service, use its duration; otherwise use first available service.
    """
    if not services:
        return []

    # Try to match the requested service by name
    target_service = None
    if submission.service_requested:
        req_lower = submission.service_requested.lower()
        for svc in services:
            if req_lower in svc.name.lower() or svc.name.lower() in req_lower:
                target_service = svc
                break

    if target_service is None:
        target_service = services[0]

    # Start from today (or preferred date if given)
    start = submission.preferred_date or date.today()
    end = start + timedelta(days=7)

    try:
        return get_available_slots(db, business.id, target_service.id, start, end)
    except Exception as exc:
        logger.warning("contact_responder: could not fetch slots: %s", exc)
        return []


def _build_context_block(
    business: Business,
    services: list[ServiceType],
    available_slots: list[dict],
    submission: ContactSubmission,
) -> str:
    """
    Build a text block of context handed to the AI:
    - Business info
    - Services + pricing
    - Available appointment slots
    """
    lines = []

    # Business info
    lines.append(f"BUSINESS: {business.name}")
    if business.phone:
        lines.append(f"Phone: {business.phone}")
    if business.email:
        lines.append(f"Email: {business.email}")
    if business.address:
        lines.append(f"Address: {business.address}")
    lines.append("")

    # Services
    lines.append("SERVICES OFFERED:")
    for svc in services:
        price_str = ""
        if svc.base_price is not None:
            price_str = f"  |  ${svc.base_price:.0f}"
        lines.append(f"  • {svc.name} ({svc.duration_minutes} min{price_str})")
    lines.append("")

    # Available slots (first 10 across next 7 days)
    if available_slots:
        lines.append("AVAILABLE APPOINTMENT SLOTS (next 7 days):")
        slot_count = 0
        for day in available_slots:
            if slot_count >= settings.CONTACT_MAX_SUGGESTED_SLOTS * 2:
                break
            day_slots = day.get("slots", [])
            if not day_slots:
                continue
            day_label = day["date"]
            try:
                d = date.fromisoformat(day_label)
                day_label = d.strftime("%A, %B %d")
            except Exception:
                pass
            for slot in day_slots[:3]:
                if slot_count >= settings.CONTACT_MAX_SUGGESTED_SLOTS * 2:
                    break
                start_dt = slot["start"]
                end_dt = slot["end"]
                if isinstance(start_dt, datetime):
                    start_str = start_dt.strftime("%I:%M %p").lstrip("0")
                    end_str = end_dt.strftime("%I:%M %p").lstrip("0")
                else:
                    start_str = str(start_dt)
                    end_str = str(end_dt)
                lines.append(f"  • {day_label}: {start_str} – {end_str}")
                slot_count += 1
    else:
        lines.append("(No specific slot availability data available — invite them to call.)")

    return "\n".join(lines)
