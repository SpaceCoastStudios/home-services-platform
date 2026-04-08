"""
SMS AI Booking Agent.

Flow per inbound message:
1. Look up the business by To (Twilio number).
2. Load or create the SmsConversation for (business, customer_phone).
3. Append the new user message to the thread.
4. Build a context-aware system prompt from business info + live availability.
5. Call Claude with tool_use: check_availability, create_booking, escalate_to_human.
6. Handle any tool calls the model makes (execute them, feed results back).
7. Send the final assistant reply via Twilio.
8. Persist the updated conversation thread.
"""

import json
import logging
import secrets
from datetime import date, datetime, timedelta, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.config import settings
from app.models.appointment import Appointment
from app.models.business import Business
from app.models.customer import Customer
from app.models.service_type import ServiceType
from app.models.sms_conversation import SmsConversation
from app.services.scheduling import get_available_slots, auto_assign_technician

logger = logging.getLogger(__name__)

# Maximum number of recent messages passed to Claude (keeps context window manageable)
MAX_HISTORY = 20
# Target reply length hint for Claude
SMS_MAX_CHARS = 320


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def handle_inbound_sms(
    db: Session,
    business: Business,
    from_phone: str,
    body: str,
) -> str:
    """
    Process one inbound SMS message. Returns the reply text to send back.
    Raises on unrecoverable error — caller should send a fallback.
    """
    # Load or create conversation thread
    convo = _get_or_create_convo(db, business.id, from_phone)

    # Append incoming user message
    _append_message(convo, "user", body)

    if not settings.ANTHROPIC_API_KEY:
        reply = (
            f"Hi! Thanks for reaching out to {business.name}. "
            "We'll get back to you shortly."
        )
        _append_message(convo, "assistant", reply)
        _save_convo(db, convo)
        return reply

    try:
        reply = _run_agent(db, business, convo)
    except Exception as exc:
        logger.error("sms_agent: error for convo %s: %s", convo.id, exc, exc_info=True)
        reply = (
            f"Sorry, I ran into a hiccup. Please call {business.phone or business.name} "
            "directly and we'll get you sorted out."
        )

    _append_message(convo, "assistant", reply)
    _save_convo(db, convo)
    return reply


# ---------------------------------------------------------------------------
# Agent loop — calls Claude with tool_use, executes tools, gets final reply
# ---------------------------------------------------------------------------

def _run_agent(db: Session, business: Business, convo: SmsConversation) -> str:
    import anthropic

    client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

    services = _get_active_services(db, business.id)
    system_prompt = _build_system_prompt(business, services)
    messages = _build_messages(convo)

    tools = _define_tools(services)

    # Agentic loop — Claude may call tools before producing a final reply
    for iteration in range(5):  # guard against infinite loops
        response = client.messages.create(
            model=settings.LLM_MODEL,
            max_tokens=512,
            system=system_prompt,
            tools=tools,
            messages=messages,
        )

        # Collect text and tool_use blocks
        text_parts = []
        tool_calls = []
        for block in response.content:
            if block.type == "text":
                text_parts.append(block.text)
            elif block.type == "tool_use":
                tool_calls.append(block)

        # If no tool calls, we have the final reply
        if not tool_calls:
            reply = " ".join(text_parts).strip()
            return reply[:SMS_MAX_CHARS] if len(reply) > SMS_MAX_CHARS else reply

        # Execute each tool call and collect results
        tool_results = []
        for tc in tool_calls:
            result = _execute_tool(db, business, convo, tc.name, tc.input)
            tool_results.append({
                "type": "tool_result",
                "tool_use_id": tc.id,
                "content": json.dumps(result),
            })

        # Append assistant turn + tool results, then loop
        messages.append({"role": "assistant", "content": response.content})
        messages.append({"role": "user", "content": tool_results})

    # Fallback if loop limit hit
    return f"I'd be happy to help you book with {business.name}. Please call us directly to confirm your appointment."


# ---------------------------------------------------------------------------
# Tool definitions
# ---------------------------------------------------------------------------

def _define_tools(services: list[ServiceType]) -> list[dict]:
    service_names = [s.name for s in services] if services else ["General Service"]
    return [
        {
            "name": "check_availability",
            "description": (
                "Check available appointment slots for a specific service. "
                "Call this when the customer asks about availability or wants to book."
            ),
            "input_schema": {
                "type": "object",
                "properties": {
                    "service_name": {
                        "type": "string",
                        "description": f"The service to check. Known services: {', '.join(service_names)}",
                    },
                    "days_ahead": {
                        "type": "integer",
                        "description": "How many days ahead to check (default 7, max 14).",
                        "default": 7,
                    },
                },
                "required": ["service_name"],
            },
        },
        {
            "name": "create_booking",
            "description": (
                "Create an appointment booking. Only call this when you have confirmed ALL of: "
                "customer name, service, date and time, and service address. "
                "Always confirm details with the customer before calling this."
            ),
            "input_schema": {
                "type": "object",
                "properties": {
                    "customer_name": {
                        "type": "string",
                        "description": "Customer's full name.",
                    },
                    "service_name": {
                        "type": "string",
                        "description": "The service being booked.",
                    },
                    "appointment_datetime": {
                        "type": "string",
                        "description": "ISO 8601 datetime string (e.g. 2026-04-15T10:00:00).",
                    },
                    "address": {
                        "type": "string",
                        "description": "Service address.",
                    },
                    "notes": {
                        "type": "string",
                        "description": "Any additional notes from the customer.",
                    },
                },
                "required": ["customer_name", "service_name", "appointment_datetime", "address"],
            },
        },
        {
            "name": "escalate_to_human",
            "description": (
                "Flag this conversation for human follow-up. Use when: the customer is upset, "
                "the request is outside normal services, pricing negotiation is needed, "
                "or you cannot resolve the issue after 2 attempts."
            ),
            "input_schema": {
                "type": "object",
                "properties": {
                    "reason": {
                        "type": "string",
                        "description": "Brief reason why human follow-up is needed.",
                    },
                },
                "required": ["reason"],
            },
        },
    ]


# ---------------------------------------------------------------------------
# Tool execution
# ---------------------------------------------------------------------------

def _execute_tool(
    db: Session,
    business: Business,
    convo: SmsConversation,
    tool_name: str,
    tool_input: dict,
) -> dict:
    logger.info("sms_agent: executing tool %s for convo %s", tool_name, convo.id)

    if tool_name == "check_availability":
        return _tool_check_availability(db, business, tool_input)

    elif tool_name == "create_booking":
        return _tool_create_booking(db, business, convo, tool_input)

    elif tool_name == "escalate_to_human":
        convo.status = "escalated"
        reason = tool_input.get("reason", "No reason given")
        logger.info("sms_agent: convo %s escalated — %s", convo.id, reason)
        return {"escalated": True, "reason": reason}

    return {"error": f"Unknown tool: {tool_name}"}


def _tool_check_availability(db: Session, business: Business, inp: dict) -> dict:
    services = _get_active_services(db, business.id)
    service_name = inp.get("service_name", "")
    days_ahead = min(int(inp.get("days_ahead", 7)), 14)

    # Match service by name (fuzzy)
    service = None
    name_lower = service_name.lower()
    for s in services:
        if name_lower in s.name.lower() or s.name.lower() in name_lower:
            service = s
            break
    if service is None and services:
        service = services[0]

    if not service:
        return {"error": "No active services found for this business."}

    start = date.today()
    end = start + timedelta(days=days_ahead)

    try:
        raw_slots = get_available_slots(db, business.id, service.id, start, end)
    except Exception as exc:
        logger.warning("sms_agent: check_availability error: %s", exc)
        return {"error": "Could not retrieve availability. Ask the customer to call."}

    # Flatten to a readable list (max 10 slots)
    slots = []
    for day in raw_slots:
        for slot in day.get("slots", []):
            if len(slots) >= 10:
                break
            start_dt = slot["start"]
            if isinstance(start_dt, datetime):
                slots.append({
                    "date": start_dt.strftime("%A, %B %d"),
                    "time": start_dt.strftime("%I:%M %p").lstrip("0"),
                    "iso": start_dt.isoformat(),
                })
        if len(slots) >= 10:
            break

    return {
        "service": service.name,
        "duration_minutes": service.duration_minutes,
        "price": float(service.base_price) if service.base_price else None,
        "available_slots": slots,
    }


def _tool_create_booking(
    db: Session, business: Business, convo: SmsConversation, inp: dict
) -> dict:
    services = _get_active_services(db, business.id)

    # Match service
    service_name = inp.get("service_name", "")
    service = None
    for s in services:
        if service_name.lower() in s.name.lower() or s.name.lower() in service_name.lower():
            service = s
            break
    if service is None and services:
        service = services[0]
    if not service:
        return {"error": "Could not find a matching service."}

    # Parse datetime
    try:
        appt_start = datetime.fromisoformat(inp["appointment_datetime"])
        # Ensure UTC-aware
        if appt_start.tzinfo is None:
            appt_start = appt_start.replace(tzinfo=timezone.utc)
    except (ValueError, KeyError) as exc:
        return {"error": f"Invalid appointment datetime: {exc}"}

    appt_end = appt_start + timedelta(minutes=service.duration_minutes)

    # Find or create Customer by phone
    customer = (
        db.query(Customer)
        .filter(Customer.phone == convo.customer_phone, Customer.business_id == business.id)
        .first()
    )
    if not customer:
        name_parts = inp.get("customer_name", "SMS Customer").split(None, 1)
        first = name_parts[0]
        last = name_parts[1] if len(name_parts) > 1 else ""
        customer = Customer(
            business_id=business.id,
            first_name=first,
            last_name=last,
            phone=convo.customer_phone,
        )
        db.add(customer)
        db.flush()

    # Update learned name on the conversation
    convo.customer_name = inp.get("customer_name") or convo.customer_name

    # Auto-assign technician
    tech_id = auto_assign_technician(
        db, business.id, service.id, appt_start, appt_end
    )

    # Create appointment
    appointment = Appointment(
        business_id=business.id,
        customer_id=customer.id,
        service_type_id=service.id,
        technician_id=tech_id,
        scheduled_start=appt_start,
        scheduled_end=appt_end,
        status="pending",
        source="sms",
        address=inp.get("address", ""),
        notes=inp.get("notes", "Booked via SMS"),
        calendar_token=secrets.token_urlsafe(48),
    )
    db.add(appointment)
    db.flush()

    # Update conversation status and link to appointment
    convo.status = "booked"
    convo.appointment_id = appointment.id

    # Send confirmation SMS
    _send_booking_confirmation(business, customer, appointment, service)

    db.commit()

    logger.info(
        "sms_agent: booking created — appt_id=%s, business=%s, customer=%s",
        appointment.id, business.slug, customer.id,
    )

    return {
        "success": True,
        "appointment_id": appointment.id,
        "service": service.name,
        "date": appt_start.strftime("%A, %B %d"),
        "time": appt_start.strftime("%I:%M %p").lstrip("0"),
        "address": inp.get("address", ""),
    }


# ---------------------------------------------------------------------------
# Confirmation SMS
# ---------------------------------------------------------------------------

def _send_booking_confirmation(
    business: Business, customer: Customer, appointment: Appointment, service: ServiceType
) -> None:
    twilio_number = business.twilio_phone_number or settings.TWILIO_PHONE_NUMBER
    if not settings.TWILIO_ACCOUNT_SID or not twilio_number or not customer.phone:
        return

    try:
        from twilio.rest import Client
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        date_str = appointment.scheduled_start.strftime("%a %b %d at %I:%M %p").replace(" 0", " ")
        body = (
            f"✓ Confirmed! {service.name} with {business.name} on {date_str}. "
            f"Address: {appointment.address}. "
            f"Questions? Reply or call {business.phone or 'us'}."
        )
        client.messages.create(body=body, from_=twilio_number, to=customer.phone)
    except Exception as exc:
        logger.error("sms_agent: failed to send booking confirmation: %s", exc)


# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------

def _build_system_prompt(business: Business, services: list[ServiceType]) -> str:
    agent_name = business.ai_agent_name or f"{business.name} Assistant"
    custom_prompt = business.ai_system_prompt or ""

    service_lines = "\n".join(
        f"  • {s.name} ({s.duration_minutes} min"
        + (f", ${s.base_price:.0f}" if s.base_price else "")
        + ")"
        for s in services
    ) or "  • General service"

    return f"""You are {agent_name}, a friendly booking assistant for {business.name}. \
You communicate only via SMS, so keep every reply SHORT — under 2-3 sentences ideally, \
never more than 320 characters. No emojis, no markdown, just plain conversational text.

Your goal is to book appointments. To do that you need:
1. Customer's name
2. Which service they need
3. A date and time that works for them
4. Their service address

Collect these naturally through conversation — don't fire all questions at once.
Use the check_availability tool before suggesting times.
Use the create_booking tool only once you have all 4 pieces confirmed.
Use escalate_to_human if you can't resolve something after 2 attempts.

{custom_prompt}

SERVICES OFFERED BY {business.name.upper()}:
{service_lines}

Business phone: {business.phone or "See website"}
Always be warm, efficient, and professional. Never make up availability — use the tool."""


# ---------------------------------------------------------------------------
# Conversation helpers
# ---------------------------------------------------------------------------

def _get_or_create_convo(db: Session, business_id: int, customer_phone: str) -> SmsConversation:
    convo = (
        db.query(SmsConversation)
        .filter(
            SmsConversation.business_id == business_id,
            SmsConversation.customer_phone == customer_phone,
            SmsConversation.status == "active",
        )
        .order_by(SmsConversation.last_message_at.desc())
        .first()
    )
    if not convo:
        convo = SmsConversation(
            business_id=business_id,
            customer_phone=customer_phone,
            messages=[],
            status="active",
        )
        db.add(convo)
        db.flush()
    return convo


def _append_message(convo: SmsConversation, role: str, content: str) -> None:
    messages = list(convo.messages or [])
    messages.append({
        "role": role,
        "content": content,
        "ts": datetime.now(timezone.utc).isoformat(),
    })
    convo.messages = messages
    convo.last_message_at = datetime.now(timezone.utc)


def _build_messages(convo: SmsConversation) -> list[dict]:
    """Convert stored thread to Anthropic messages format (last MAX_HISTORY turns)."""
    raw = convo.messages or []
    recent = raw[-MAX_HISTORY:]
    return [{"role": m["role"], "content": m["content"]} for m in recent]


def _save_convo(db: Session, convo: SmsConversation) -> None:
    db.add(convo)
    db.commit()
    db.refresh(convo)


def _get_active_services(db: Session, business_id: int) -> list[ServiceType]:
    return (
        db.query(ServiceType)
        .filter(ServiceType.business_id == business_id, ServiceType.is_active == True)
        .order_by(ServiceType.name)
        .all()
    )
