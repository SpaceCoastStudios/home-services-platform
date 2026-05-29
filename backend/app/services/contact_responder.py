"""
AI contact form auto-responder.
"""

import json
import logging
from datetime import date, datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.config import settings
from app.models.business import Business
from app.models.contact_submission import ContactSubmission
from app.models.service_type import ServiceType
from app.services.scheduling import get_available_slots

logger = logging.getLogger(__name__)


def run_contact_responder(db: Session, submission_id: int) -> None:
    from app.database import SessionLocal
    own_db = SessionLocal()
    try:
        submission = own_db.query(ContactSubmission).filter(ContactSubmission.id == submission_id).first()
        if not submission:
            logger.error("contact_responder: submission %s not found", submission_id)
            return
        business = own_db.query(Business).filter(Business.id == submission.business_id).first()
        if not business:
            logger.error("contact_responder: business %s not found", submission.business_id)
            return
        if not settings.ANTHROPIC_API_KEY:
            logger.warning("contact_responder: ANTHROPIC_API_KEY not set -- skipping AI response")
            return
        try:
            _process(own_db, submission, business)
        except Exception as exc:
            logger.error("contact_responder: unhandled error for submission %s: %s", submission_id, exc, exc_info=True)
            submission.status = "error"
            own_db.commit()
    finally:
        own_db.close()


def _process(db: Session, submission: ContactSubmission, business: Business) -> None:
    sms_consented = getattr(submission, "sms_consent", False)
    raw_pref = (submission.preferred_contact_method or "").lower()
    pref = raw_pref if not (raw_pref == "text" and not sms_consented) else "email"

    services = _get_active_services(db, business.id)
    available_slots = _get_upcoming_slots(db, business, submission, services)
    context_block = _build_context_block(business, services, available_slots, submission)

    ai_result = _call_llm(business, submission, context_block, pref)
    reply_text = ai_result.get("reply", "")
    suggested_slots = ai_result.get("suggested_slots", [])

    if not reply_text:
        logger.warning("contact_responder: LLM returned empty reply for submission %s", submission.id)
        return

    submission.ai_response = reply_text
    submission.ai_suggested_slots = suggested_slots if suggested_slots else None

    draft_only = getattr(business, "ai_response_mode", "auto_send") == "draft_only"
    if draft_only:
        submission.status = "pending_approval"
        db.commit()
        logger.info("contact_responder: submission %s drafted (pending approval) for business %s", submission.id, business.slug)
        return

    use_sms = (pref == "text" and sms_consented and bool(submission.phone))

    email_sent = False
    sms_sent = False

    if use_sms:
        sms_sent = _send_reply_sms(business, submission, reply_text)
    else:
        email_sent = _send_reply_email(business, submission, reply_text)
        if pref == "text" and not sms_consented:
            logger.info("contact_responder: submission %s preferred text but no SMS consent -- replied by email", submission.id)

    submission.status = "ai_responded"
    submission.responded_at = datetime.now(timezone.utc)
    db.commit()
    logger.info(
        "contact_responder: completed submission %s for business %s (channel=%s, email_sent=%s, sms_sent=%s)",
        submission.id, business.slug, "sms" if use_sms else "email", email_sent, sms_sent,
    )


def _call_llm(business: Business, submission: ContactSubmission, context_block: str, pref: str) -> dict:
    import anthropic

    agent_name = business.ai_agent_name or business.name
    business_system_prompt = business.ai_system_prompt or ""

    if pref == "text":
        contact_pref_label = "text message (SMS)"
        closing_instruction = (
            "They prefer text messages and your reply will be sent as an SMS. "
            "Keep the ENTIRE reply under 400 characters -- be warm but brief. "
            "Skip a long acknowledgment; get straight to 1-2 available slots and a CTA. "
            "Close by inviting them to reply to this text with their preferred slot. Do NOT mention email."
        )
    elif pref == "call":
        contact_pref_label = "phone call"
        closing_instruction = (
            "They prefer a phone call -- close by letting them know you will be in touch "
            "by phone, and include the business phone number ({}) "
            "in case they want to call first. Do NOT say reply to this email.".format(
                business.phone or "on file"
            )
        )
    elif pref == "email":
        contact_pref_label = "email"
        closing_instruction = (
            "They prefer email -- close by inviting them to reply to this email "
            "with their preferred slot."
        )
    else:
        contact_pref_label = "not specified"
        closing_instruction = "Invite them to call or reply by email to confirm their preferred slot."

    system_prompt = (
        "You are {agent}, a friendly and professional customer service assistant for {biz}.\n\n"
        "Your job is to respond to customer inquiries submitted through the website contact form.\n"
        "Write warm, helpful, and professional replies -- as if a knowledgeable human staff member wrote them.\n"
        "Keep responses concise (3-5 short paragraphs max).\n\n"
        "The customer preferred contact method is: {pref_label}.\n"
        "When closing the reply, reference ONLY their preferred channel. Never mention a channel they did not choose.\n\n"
        "{biz_prompt}\n\n"
        "--- CONTEXT ---\n"
        "{context}\n"
        "--- END CONTEXT ---\n\n"
        "RESPONSE FORMAT:\n"
        "Return ONLY a JSON object with two keys:\n"
        "- \"reply\": A plain-text reply to the customer. Use \\n for line breaks. Do NOT include HTML.\n"
        "- \"suggested_slots\": An optional JSON array of up to {max_slots} available time slots you mentioned in the reply.\n"
        "  Each slot: {{\"date\": \"YYYY-MM-DD\", \"start\": \"HH:MM\", \"end\": \"HH:MM\"}}\n"
        "  Leave as an empty array [] if you did not suggest specific slots.\n\n"
        "Return ONLY the JSON object. No markdown, no code blocks, no extra text."
    ).format(
        agent=agent_name,
        biz=business.name,
        pref_label=contact_pref_label,
        biz_prompt=business_system_prompt,
        context=context_block,
        max_slots=settings.CONTACT_MAX_SUGGESTED_SLOTS,
    )

    problem_block = ""
    if submission.problem_description:
        problem_block = "\nProblem description:\n{}\n".format(submission.problem_description)

    user_message = (
        "New customer inquiry:\n\n"
        "Name: {name}\n"
        "Email: {email}\n"
        "Phone: {phone}\n"
        "Service requested: {service}\n"
        "Preferred contact method: {pref_label}\n"
        "Preferred date: {pref_date}\n"
        "Preferred time: {pref_time}\n\n"
        "Message:\n{message}\n"
        "{problem_block}\n"
        "Please write a helpful, friendly reply. If they seem interested in booking, "
        "mention 2-3 specific available time slots from the context. {closing}"
    ).format(
        name=submission.name,
        email=submission.email,
        phone=submission.phone or "Not provided",
        service=submission.service_requested or "Not specified",
        pref_label=contact_pref_label,
        pref_date=submission.preferred_date or "Not specified",
        pref_time=submission.preferred_time or "Not specified",
        message=submission.message,
        problem_block=problem_block,
        closing=closing_instruction,
    )

    client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
    response = client.messages.create(
        model=settings.LLM_MODEL,
        max_tokens=1024,
        system=system_prompt,
        messages=[{"role": "user", "content": user_message}],
    )

    raw = response.content[0].text.strip()
    logger.debug("contact_responder LLM raw output: %s", raw[:500])

    if raw.startswith("```"):
        lines_list = raw.split("\n")
        raw = "\n".join(lines_list[1:-1]) if lines_list[-1].strip() == "```" else "\n".join(lines_list[1:])

    try:
        parsed = json.loads(raw)
        return {"reply": parsed.get("reply", ""), "suggested_slots": parsed.get("suggested_slots", [])}
    except json.JSONDecodeError:
        logger.warning("contact_responder: LLM response was not valid JSON -- using raw text as reply")
        return {"reply": raw, "suggested_slots": []}


def _send_reply_email(business: Business, submission: ContactSubmission, reply_text: str) -> bool:
    if not settings.SENDGRID_API_KEY:
        logger.warning("contact_responder: SendGrid not configured -- skipping email")
        return False
    try:
        import sendgrid
        from sendgrid.helpers.mail import Mail, Email, To, Content

        from_email = business.from_email or settings.sender_email
        from_name = business.ai_agent_name or business.name or settings.sender_name
        html_body = _build_reply_html(business, submission, reply_text)

        sg = sendgrid.SendGridAPIClient(api_key=settings.SENDGRID_API_KEY)
        mail = Mail(
            from_email=Email(from_email, from_name),
            to_emails=To(submission.email),
            subject="Re: Your inquiry to {}".format(business.name),
            html_content=Content("text/html", html_body),
        )
        import ssl as _ssl
        _orig = _ssl._create_default_https_context
        _ssl._create_default_https_context = _ssl._create_unverified_context
        try:
            response = sg.client.mail.send.post(request_body=mail.get())
        finally:
            _ssl._create_default_https_context = _orig
        logger.info("contact_responder: reply email sent to %s (status=%s)", submission.email, response.status_code)
        return True
    except Exception as exc:
        logger.error("contact_responder: failed to send reply email to %s: %s", submission.email, exc)
        return False


def _send_reply_sms(business: Business, submission: ContactSubmission, reply_text: str) -> bool:
    twilio_number = business.twilio_phone_number or settings.TWILIO_PHONE_NUMBER
    if not settings.TWILIO_ACCOUNT_SID or not twilio_number:
        return False
    try:
        from twilio.rest import Client
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)

        paragraphs = [p.strip() for p in reply_text.split("\n\n") if p.strip()]
        if len(paragraphs) > 1:
            first = paragraphs[0]
            if len(first) < 30 and first.endswith(","):
                paragraphs = paragraphs[1:]

        sms_content = " ".join(p.replace("\n", " ") for p in paragraphs)

        MAX_SMS = 480
        if len(sms_content) > MAX_SMS:
            sms_content = sms_content[:MAX_SMS - 3] + "..."

        client.messages.create(body=sms_content, from_=twilio_number, to=submission.phone)
        logger.info("contact_responder: reply SMS sent to %s (%d chars)", submission.phone, len(sms_content))
        return True
    except Exception as exc:
        logger.error("contact_responder: failed to send reply SMS to %s: %s", submission.phone, exc)
        return False


def _build_reply_html(business: Business, submission: ContactSubmission, reply_text: str) -> str:
    brand_color = business.brand_color or "#2563eb"
    agent_name = business.ai_agent_name or business.name
    business_name = business.name

    paragraphs = [p.strip() for p in reply_text.split("\n\n") if p.strip()]
    body_html = "".join(
        "<p style=\'margin:0 0 14px 0;\'>{}</p>".format(p.replace("\n", "<br>"))
        for p in paragraphs
    )

    contact_line = ""
    if business.phone:
        contact_line += "<a href=\'tel:{p}\' style=\'color:{c};\'>{p}</a>".format(p=business.phone, c=brand_color)
    if business.email:
        sep = " &nbsp;|&nbsp; " if contact_line else ""
        contact_line += "{sep}<a href=\'mailto:{e}\' style=\'color:{c};\'>{e}</a>".format(sep=sep, e=business.email, c=brand_color)
    if business.website:
        sep = " &nbsp;|&nbsp; " if contact_line else ""
        contact_line += "{sep}<a href=\'{w}\' style=\'color:{c};\'>{w}</a>".format(sep=sep, w=business.website, c=brand_color)

    first_name = submission.name.split()[0] if submission.name else submission.name

    html = """<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="margin:0;padding:0;background:#f3f4f6;font-family:sans-serif;">
  <div style="max-width:600px;margin:32px auto;">
    <div style="background:{color};color:white;padding:24px 28px;border-radius:8px 8px 0 0;">
      <h1 style="margin:0;font-size:20px;">{biz_name}</h1>
    </div>
    <div style="background:white;padding:28px;border:1px solid #e5e7eb;border-top:none;">
      <p style="margin:0 0 16px 0;color:#374151;">Hi {first_name},</p>
      {body_html}
      <p style="margin:20px 0 0 0;color:#6b7280;font-size:13px;">-- {agent_name}</p>
    </div>
    <div style="background:#f9fafb;padding:16px 28px;border:1px solid #e5e7eb;border-top:none;border-radius:0 0 8px 8px;text-align:center;">
      <p style="margin:0;font-size:12px;color:#9ca3af;">{contact_line}</p>
      <p style="margin:8px 0 0 0;font-size:11px;color:#d1d5db;">You received this because you submitted a contact form on our website.</p>
    </div>
  </div>
</body>
</html>""".format(
        color=brand_color, biz_name=business_name, first_name=first_name,
        body_html=body_html, agent_name=agent_name, contact_line=contact_line,
    )
    return html


def _get_active_services(db: Session, business_id: int) -> list:
    return (
        db.query(ServiceType)
        .filter(ServiceType.business_id == business_id, ServiceType.is_active == True)
        .order_by(ServiceType.name)
        .all()
    )


def _get_upcoming_slots(db: Session, business: Business, submission: ContactSubmission, services: list) -> list:
    if not services:
        return []
    target_service = None
    if submission.service_requested:
        req_lower = submission.service_requested.lower()
        for svc in services:
            if req_lower in svc.name.lower() or svc.name.lower() in req_lower:
                target_service = svc
                break
    if target_service is None:
        target_service = services[0]
    start = submission.preferred_date or date.today()
    end = start + timedelta(days=7)
    try:
        return get_available_slots(db, business.id, target_service.id, start, end)
    except Exception as exc:
        logger.warning("contact_responder: could not fetch slots: %s", exc)
        return []


def _build_context_block(business: Business, services: list, available_slots: list, submission: ContactSubmission) -> str:
    lines = []
    lines.append("BUSINESS: {}".format(business.name))
    if business.phone:
        lines.append("Phone: {}".format(business.phone))
    if business.email:
        lines.append("Email: {}".format(business.email))
    if business.address:
        lines.append("Address: {}".format(business.address))
    lines.append("")
    lines.append("SERVICES OFFERED:")
    for svc in services:
        price_str = ""
        if svc.base_price is not None:
            price_str = "  |  ${:.0f}".format(svc.base_price)
        lines.append("  - {} ({} min{})".format(svc.name, svc.duration_minutes, price_str))
    lines.append("")
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
                lines.append("  - {}: {} - {}".format(day_label, start_str, end_str))
                slot_count += 1
    else:
        lines.append("(No specific slot availability data available -- invite them to call.)")
    return "\n".join(lines)
