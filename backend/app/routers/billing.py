"""
Stripe billing endpoints.

Public (no auth):
  POST /api/billing/checkout          — create a Stripe Checkout session (marketing site)
  GET  /api/billing/checkout-session  — retrieve session email for welcome page
  POST /api/billing/webhook           — Stripe webhook handler (provision tenant on payment)

JWT-protected:
  GET  /api/billing/subscription      — current plan / status for the active business
  POST /api/billing/portal            — create a Stripe Customer Portal session
"""

import hashlib
import hmac
import logging
import re
import secrets
from datetime import datetime, timedelta, timezone

import stripe
from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.admin_user import AdminUser
from app.models.business import Business
from app.utils.auth import get_current_user, get_business_id_for_user, hash_password

logger = logging.getLogger(__name__)

router = APIRouter(tags=["billing"])

DASHBOARD_URL = "https://dashboard.spacecoaststudios.com"
MARKETING_URL = "https://spacecoaststudios.com"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _stripe_client():
    if not settings.STRIPE_SECRET_KEY:
        raise HTTPException(status_code=503, detail="Stripe not configured")
    stripe.api_key = settings.STRIPE_SECRET_KEY
    return stripe


PLAN_PRICES = {
    "starter": {
        "setup":   settings.STRIPE_PRICE_STARTER_SETUP,
        "monthly": settings.STRIPE_PRICE_STARTER_MONTHLY,
    },
    "professional": {
        "setup":   settings.STRIPE_PRICE_PRO_SETUP,
        "monthly": settings.STRIPE_PRICE_PRO_MONTHLY,
    },
    "test": {
        "setup":   "price_1TbkYi2MJMR8rAcZO4iP0oHP",
        "monthly": "price_1TbkkP2MJMR8rAcZAPo5kJx5",
    },
}


def _slugify(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower().strip()).strip("-")
    return slug[:80] or "business"


def _unique_slug(db: Session, base: str) -> str:
    slug = base
    counter = 1
    while db.query(Business).filter(Business.slug == slug).first():
        slug = f"{base}-{counter}"
        counter += 1
    return slug


def _send_welcome_email(email: str, business_name: str, token: str):
    """Send the set-your-password welcome email via SendGrid."""
    from app.services.notifications import send_email
    set_password_url = f"{DASHBOARD_URL}/set-password?token={token}"
    subject = f"Welcome to Launchpad — Set up your account"
    plain = (
        f"Hi,\n\n"
        f"Your account for {business_name} has been created on the Launchpad platform by Space Coast Studios.\n\n"
        f"Your login username is: {email}\n\n"
        f"Click the link below to set your password and access your dashboard:\n"
        f"{set_password_url}\n\n"
        f"This link expires in 72 hours.\n\n"
        f"If you have any questions, reply to this email or contact us at support@spacecoaststudios.com.\n\n"
        f"— Launchpad by Space Coast Studios"
    )
    html = f"""
    <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;padding:32px;">
      <h2 style="color:#1e40af;">Welcome to Launchpad!</h2>
      <p>Your account for <strong>{business_name}</strong> has been created.</p>
      <p style="margin:20px 0;padding:16px;background:#f0f9ff;border-radius:8px;border-left:4px solid #2563eb;">
        <span style="font-size:12px;color:#6b7280;text-transform:uppercase;letter-spacing:0.05em;">Your login username</span><br>
        <strong style="font-size:16px;color:#1e293b;">{email}</strong>
      </p>
      <p>Click the button below to set your password and access your dashboard:</p>
      <p style="text-align:center;margin:32px 0;">
        <a href="{set_password_url}"
           style="background:#2563eb;color:#fff;padding:14px 28px;border-radius:8px;
                  text-decoration:none;font-weight:bold;font-size:16px;">
          Set Your Password
        </a>
      </p>
      <p style="color:#6b7280;font-size:13px;">This link expires in 72 hours.<br>
         If you didn't sign up for this service, you can ignore this email.</p>
      <hr style="border:none;border-top:1px solid #e5e7eb;margin:24px 0;">
      <p style="color:#9ca3af;font-size:12px;">Launchpad by Space Coast Studios &mdash; support@spacecoaststudios.com</p>
    </div>
    """
    try:
        send_email(email, subject, html, plain)
        logger.info("Welcome email sent to %s", email)
    except Exception as exc:
        logger.error("Failed to send welcome email to %s: %s", email, exc)


def _provision_tenant(db: Session, session: dict):
    """
    Create a Business + AdminUser from a completed Stripe Checkout session.
    Idempotent — skips if stripe_customer_id already exists.
    """
    customer_id  = session.get("customer")
    subscription_id = session.get("subscription")
    plan         = (session.get("metadata") or {}).get("plan", "starter")

    # Pull custom fields
    custom_fields = {cf["key"]: cf.get("text", {}).get("value", "") for cf in (session.get("custom_fields") or [])}
    business_name = custom_fields.get("businessname") or custom_fields.get("business_name") or "New Business"
    phone         = custom_fields.get("phone") or ""

    # customer_details holds email, phone, and address from Stripe Checkout
    details = session.get("customer_details") or {}

    # Email: prefer customer_details.email (set by Stripe Checkout), fall back to customer_email
    email = details.get("email") or session.get("customer_email") or ""
    addr_obj = details.get("address") or {}
    address_parts = [addr_obj.get("line1"), addr_obj.get("city"), addr_obj.get("state"), addr_obj.get("postal_code")]
    address = ", ".join(p for p in address_parts if p)

    # Idempotency guard
    if db.query(Business).filter(Business.stripe_customer_id == customer_id).first():
        logger.info("Provision skipped — customer %s already exists", customer_id)
        return

    # Fetch subscription to get period_end
    period_end = None
    if subscription_id:
        try:
            stripe.api_key = settings.STRIPE_SECRET_KEY
            sub = stripe.Subscription.retrieve(subscription_id)
            pe = sub.get("current_period_end")
            if pe:
                period_end = datetime.fromtimestamp(pe, tz=timezone.utc)
        except Exception as exc:
            logger.warning("Could not fetch subscription period_end: %s", exc)

    # Create Business
    slug = _unique_slug(db, _slugify(business_name))
    business = Business(
        name=business_name,
        slug=slug,
        phone=phone,
        email=email,
        address=address,
        stripe_customer_id=customer_id,
        stripe_subscription_id=subscription_id,
        subscription_tier=plan,
        subscription_status="active",
        subscription_period_end=period_end,
        is_active=True,
        is_demo=False,
    )
    db.add(business)
    db.flush()  # get business.id

    # Create AdminUser (username = email)
    reset_token = secrets.token_urlsafe(48)
    expires = datetime.now(timezone.utc) + timedelta(hours=72)
    admin = AdminUser(
        business_id=business.id,
        username=email,
        email=email,
        password_hash=hash_password(secrets.token_urlsafe(32)),  # unusable until set
        role="admin",
        is_active=True,
        password_reset_token=reset_token,
        password_reset_expires=expires,
    )
    db.add(admin)
    db.commit()

    logger.info("Provisioned tenant: business=%d slug=%s email=%s plan=%s", business.id, slug, email, plan)

    # Send welcome email with set-password link
    _send_welcome_email(email, business_name, reset_token)


# ---------------------------------------------------------------------------
# POST /api/billing/checkout
# ---------------------------------------------------------------------------

@router.post("/api/billing/checkout")
def create_checkout_session(body: dict):
    """
    Create a Stripe Checkout session.
    Called from the marketing site pricing buttons.

    Body: { "plan": "starter" | "professional" }
    Returns: { "url": "https://checkout.stripe.com/..." }
    """
    plan = (body.get("plan") or "starter").lower()
    if plan not in PLAN_PRICES:
        raise HTTPException(status_code=400, detail="Invalid plan. Choose 'starter' or 'professional'.")

    s = _stripe_client()
    prices = PLAN_PRICES[plan]

    session = s.checkout.Session.create(
        mode="subscription",
        line_items=[
            {"price": prices["setup"],   "quantity": 1},
            {"price": prices["monthly"], "quantity": 1},
        ],
        billing_address_collection="required",
        phone_number_collection={"enabled": True},
        custom_fields=[
            {
                "key": "businessname",
                "label": {"type": "custom", "custom": "Business / DBA Name"},
                "type": "text",
            },
        ],
        metadata={"plan": plan},
        success_url=f"{DASHBOARD_URL}/welcome?session_id={{CHECKOUT_SESSION_ID}}",
        cancel_url=f"{MARKETING_URL}/#pricing",
    )

    return {"url": session.url}


# ---------------------------------------------------------------------------
# GET /api/billing/checkout-session  (welcome page — public)
# ---------------------------------------------------------------------------

@router.get("/api/billing/checkout-session")
def get_checkout_session(session_id: str):
    """
    Return minimal session info (email) for the post-checkout welcome page.
    Only exposes the customer email — nothing sensitive.
    """
    if not session_id:
        raise HTTPException(status_code=400, detail="session_id required")
    s = _stripe_client()
    try:
        session = s.checkout.Session.retrieve(session_id, expand=["customer_details"])
        email = (
            (session.get("customer_details") or {}).get("email")
            or session.get("customer_email")
            or ""
        )
        return {"email": email}
    except stripe.error.StripeError as exc:
        logger.warning("Could not retrieve checkout session %s: %s", session_id, exc)
        raise HTTPException(status_code=404, detail="Session not found")


# ---------------------------------------------------------------------------
# POST /api/billing/webhook  (Stripe → backend)
# ---------------------------------------------------------------------------

@router.post("/api/billing/webhook")
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(None, alias="stripe-signature"),
    db: Session = Depends(get_db),
):
    """Handle Stripe webhook events."""
    payload = await request.body()

    # Verify signature
    if settings.STRIPE_WEBHOOK_SECRET:
        try:
            stripe.api_key = settings.STRIPE_SECRET_KEY
            event = stripe.Webhook.construct_event(
                payload, stripe_signature, settings.STRIPE_WEBHOOK_SECRET
            )
        except stripe.error.SignatureVerificationError:
            logger.warning("Stripe webhook signature verification failed")
            raise HTTPException(status_code=400, detail="Invalid signature")
    else:
        import json
        event = json.loads(payload)
        logger.warning("STRIPE_WEBHOOK_SECRET not set — skipping signature verification")

    event_type = event["type"]
    data = event["data"]["object"]

    logger.info("Stripe webhook: %s", event_type)

    # ── Checkout completed → provision tenant ──────────────────────────────
    if event_type == "checkout.session.completed":
        _provision_tenant(db, data)

    # ── Subscription updated ───────────────────────────────────────────────
    elif event_type in ("customer.subscription.updated", "customer.subscription.deleted"):
        customer_id = data.get("customer")
        business = db.query(Business).filter(Business.stripe_customer_id == customer_id).first()
        if business:
            status_map = {
                "active":   "active",
                "past_due": "past_due",
                "canceled": "cancelled",
                "unpaid":   "unpaid",
                "trialing": "trialing",
            }
            business.subscription_status = status_map.get(data.get("status"), data.get("status"))
            if event_type == "customer.subscription.deleted":
                business.subscription_status = "cancelled"
                business.is_active = False
            pe = data.get("current_period_end")
            if pe:
                business.subscription_period_end = datetime.fromtimestamp(pe, tz=timezone.utc)
            db.commit()
            logger.info("Subscription updated for business %d: %s", business.id, business.subscription_status)

    # ── Invoice payment failed ─────────────────────────────────────────────
    elif event_type == "invoice.payment_failed":
        customer_id = data.get("customer")
        business = db.query(Business).filter(Business.stripe_customer_id == customer_id).first()
        if business:
            business.subscription_status = "past_due"
            db.commit()
            logger.warning("Payment failed for business %d", business.id)

    return {"received": True}


# ---------------------------------------------------------------------------
# GET /api/billing/subscription
# ---------------------------------------------------------------------------

@router.get("/api/billing/subscription")
def get_subscription(
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_user),
):
    """Return the current subscription status for the active business."""
    bid = get_business_id_for_user(current_user, None)
    business = db.query(Business).filter(Business.id == bid).first()
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")

    return {
        "subscription_tier":    business.subscription_tier,
        "subscription_status":  business.subscription_status,
        "subscription_period_end": (
            business.subscription_period_end.isoformat()
            if business.subscription_period_end else None
        ),
        "stripe_customer_id":   business.stripe_customer_id,
        "has_stripe":           bool(business.stripe_customer_id),
    }


# ---------------------------------------------------------------------------
# POST /api/billing/portal
# ---------------------------------------------------------------------------

@router.post("/api/billing/portal")
def create_portal_session(
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_user),
):
    """Create a Stripe Customer Portal session for managing subscription."""
    bid = get_business_id_for_user(current_user, None)
    business = db.query(Business).filter(Business.id == bid).first()

    if not business or not business.stripe_customer_id:
        raise HTTPException(status_code=400, detail="No Stripe subscription found for this business")

    s = _stripe_client()
    portal = s.billing_portal.Session.create(
        customer=business.stripe_customer_id,
        return_url=f"{DASHBOARD_URL}/billing",
    )
    return {"url": portal.url}
