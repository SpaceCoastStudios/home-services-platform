"""
Twilio inbound SMS webhook + admin SMS conversation endpoints.

Twilio webhook (public, no auth):
  POST /webhook/sms/inbound
    — Twilio posts here when a customer texts a business's Twilio number.
    — Validates the Twilio signature (when TWILIO_AUTH_TOKEN is set).
    — Looks up the business by the "To" phone number.
    — Runs the AI agent and returns TwiML with the reply.

Admin endpoints (JWT-protected):
  GET  /api/sms-conversations          — list conversations for a business
  GET  /api/sms-conversations/{id}     — get a single conversation with full thread
  POST /api/sms-conversations/{id}/close     — mark a conversation as closed
  POST /api/sms-conversations/{id}/send      — send a manual reply from the dashboard
"""

import hashlib
import hmac
import logging
from typing import Optional
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.admin_user import AdminUser
from app.models.business import Business
from app.models.sms_conversation import SmsConversation
from app.utils.auth import get_current_user, get_business_id_for_user

logger = logging.getLogger(__name__)

router = APIRouter(tags=["sms"])


# ---------------------------------------------------------------------------
# Twilio webhook — public endpoint
# ---------------------------------------------------------------------------

@router.post("/webhook/sms/inbound")
async def twilio_inbound_sms(request: Request, db: Session = Depends(get_db)):
    """
    Receives inbound SMS from Twilio.
    Validates signature, identifies business by To number, runs AI agent.
    Returns TwiML response.
    """
    body_bytes = await request.body()
    form = await request.form()

    from_phone = form.get("From", "")
    to_phone = form.get("To", "")
    message_body = form.get("Body", "").strip()

    logger.info("sms_webhook: inbound from=%s to=%s body=%r", from_phone, to_phone, message_body[:80])

    # --- Validate Twilio signature (skip in dev if no token set) ---
    if settings.TWILIO_AUTH_TOKEN:
        signature = request.headers.get("X-Twilio-Signature", "")
        url = str(request.url)
        if not _validate_twilio_signature(settings.TWILIO_AUTH_TOKEN, url, dict(form), signature):
            logger.warning("sms_webhook: invalid Twilio signature — rejecting")
            return Response(content=_twiml(""), media_type="application/xml", status_code=403)

    # --- Find business by Twilio number ---
    # Normalize to E.164 (+1XXXXXXXXXX) for comparison
    business = (
        db.query(Business)
        .filter(Business.twilio_phone_number == to_phone, Business.is_active == True)
        .first()
    )
    if not business:
        logger.warning("sms_webhook: no active business for number %s", to_phone)
        return Response(content=_twiml(""), media_type="application/xml")

    # --- Run agent ---
    if not message_body:
        reply = f"Hi! Text us at any time to book with {business.name}."
    else:
        try:
            from app.services.sms_agent import handle_inbound_sms
            reply = handle_inbound_sms(db, business, from_phone, message_body)
        except Exception as exc:
            logger.error("sms_webhook: agent error: %s", exc, exc_info=True)
            reply = (
                f"Hi, thanks for reaching out to {business.name}. "
                "We'll follow up with you shortly."
            )

    return Response(content=_twiml(reply), media_type="application/xml")


# ---------------------------------------------------------------------------
# Admin: list conversations
# ---------------------------------------------------------------------------

@router.get("/api/sms-conversations")
def list_sms_conversations(
    status: Optional[str] = None,
    business_id: Optional[int] = Query(None),
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_user),
):
    """List SMS conversations for the active business, most recent first."""
    bid = get_business_id_for_user(current_user, business_id)
    query = db.query(SmsConversation).filter(SmsConversation.business_id == bid)
    if status:
        query = query.filter(SmsConversation.status == status)
    convos = (
        query.order_by(SmsConversation.last_message_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return [_serialize_convo(c, include_messages=False) for c in convos]


# ---------------------------------------------------------------------------
# Admin: get single conversation
# ---------------------------------------------------------------------------

@router.get("/api/sms-conversations/{convo_id}")
def get_sms_conversation(
    convo_id: int,
    business_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_user),
):
    bid = get_business_id_for_user(current_user, business_id)
    convo = _get_convo_or_404(db, convo_id, bid)
    return _serialize_convo(convo, include_messages=True)


# ---------------------------------------------------------------------------
# Admin: close conversation
# ---------------------------------------------------------------------------

@router.post("/api/sms-conversations/{convo_id}/close")
def close_sms_conversation(
    convo_id: int,
    business_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_user),
):
    bid = get_business_id_for_user(current_user, business_id)
    convo = _get_convo_or_404(db, convo_id, bid)
    convo.status = "closed"
    db.commit()
    db.refresh(convo)
    return _serialize_convo(convo, include_messages=False)


# ---------------------------------------------------------------------------
# Admin: send manual reply
# ---------------------------------------------------------------------------

@router.post("/api/sms-conversations/{convo_id}/send")
def send_manual_sms(
    convo_id: int,
    body: dict,
    business_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_user),
):
    """Send a manual SMS reply from the dashboard."""
    bid = get_business_id_for_user(current_user, business_id)
    convo = _get_convo_or_404(db, convo_id, bid)

    message = body.get("message", "").strip()
    if not message:
        raise HTTPException(status_code=400, detail="message is required")

    business = db.query(Business).filter(Business.id == bid).first()
    twilio_number = business.twilio_phone_number if business else None

    if not settings.TWILIO_ACCOUNT_SID or not twilio_number:
        raise HTTPException(status_code=503, detail="Twilio not configured for this business")

    try:
        from twilio.rest import Client
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        client.messages.create(body=message, from_=twilio_number, to=convo.customer_phone)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Twilio error: {exc}")

    # Append to thread
    from datetime import datetime, timezone
    messages = list(convo.messages or [])
    messages.append({
        "role": "assistant",
        "content": message,
        "ts": datetime.now(timezone.utc).isoformat(),
        "manual": True,
    })
    convo.messages = messages
    from datetime import datetime, timezone as tz
    convo.last_message_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(convo)

    return _serialize_convo(convo, include_messages=True)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _twiml(message: str) -> str:
    """Wrap a reply in minimal TwiML. Empty message = no-op response."""
    if not message:
        return '<?xml version="1.0" encoding="UTF-8"?><Response></Response>'
    # Escape XML special characters
    safe = message.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        f"<Response><Message>{safe}</Message></Response>"
    )


def _validate_twilio_signature(auth_token: str, url: str, params: dict, signature: str) -> bool:
    """
    Validate Twilio's request signature.
    See: https://www.twilio.com/docs/usage/security#validating-signatures-from-twilio
    """
    # Build the signed string: URL + sorted POST params
    sorted_params = urlencode(sorted(params.items()))
    signed_value = url + ("?" + sorted_params if sorted_params else "")
    # Actually Twilio concatenates params without ? — params appended directly for POST
    # For POST: url + each key+value sorted alphabetically concatenated
    signed_str = url
    for key in sorted(params.keys()):
        signed_str += key + params[key]

    expected = hmac.new(
        auth_token.encode("utf-8"),
        signed_str.encode("utf-8"),
        hashlib.sha1,
    ).digest()

    import base64
    expected_b64 = base64.b64encode(expected).decode("utf-8")
    return hmac.compare_digest(expected_b64, signature)


def _get_convo_or_404(db: Session, convo_id: int, business_id: int) -> SmsConversation:
    convo = (
        db.query(SmsConversation)
        .filter(SmsConversation.id == convo_id, SmsConversation.business_id == business_id)
        .first()
    )
    if not convo:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return convo


def _serialize_convo(convo: SmsConversation, include_messages: bool = False) -> dict:
    data = {
        "id": convo.id,
        "business_id": convo.business_id,
        "customer_phone": convo.customer_phone,
        "customer_name": convo.customer_name,
        "status": convo.status,
        "appointment_id": convo.appointment_id,
        "message_count": len(convo.messages or []),
        "last_message_at": convo.last_message_at.isoformat() if convo.last_message_at else None,
        "created_at": convo.created_at.isoformat() if convo.created_at else None,
    }
    if include_messages:
        data["messages"] = convo.messages or []
    return data
