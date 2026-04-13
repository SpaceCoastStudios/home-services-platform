"""
Notification template endpoints — per-business editable SMS and email message copy.

GET  /api/notification-templates          — return all templates for a business
                                            (returns defaults for any not yet saved)
PUT  /api/notification-templates          — save one or more templates (upsert)
POST /api/notification-templates/reset    — reset all templates to platform defaults
"""

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.admin_user import AdminUser
from app.models.notification_template import NotificationTemplate, DEFAULTS, TOKENS
from app.utils.auth import get_current_user, get_business_id_for_user

router = APIRouter(tags=["notification-templates"])

ALL_KEYS = [
    ("confirmation", "sms"),
    ("confirmation", "email"),
    ("reminder_24h", "sms"),
    ("reminder_24h", "email"),
    ("review_request", "sms"),
    ("review_request", "email"),
]


def _get_templates_for_business(db: Session, business_id: int) -> list[dict]:
    """
    Return all 4 templates for a business.
    For any template not yet saved, return the platform default with is_default=True.
    """
    saved = (
        db.query(NotificationTemplate)
        .filter(NotificationTemplate.business_id == business_id)
        .all()
    )
    saved_map = {(t.event_type, t.channel): t for t in saved}

    result = []
    for event_type, channel in ALL_KEYS:
        key = (event_type, channel)
        if key in saved_map:
            t = saved_map[key]
            result.append({
                "id": t.id,
                "business_id": t.business_id,
                "event_type": t.event_type,
                "channel": t.channel,
                "subject": t.subject,
                "body": t.body,
                "is_active": t.is_active,
                "is_default": False,
            })
        else:
            default = DEFAULTS[key]
            result.append({
                "id": None,
                "business_id": business_id,
                "event_type": event_type,
                "channel": channel,
                "subject": default["subject"],
                "body": default["body"],
                "is_active": True,
                "is_default": True,
            })

    return result


@router.get("/api/notification-templates")
def get_notification_templates(
    business_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_user),
):
    """Return all templates for a business, falling back to defaults."""
    bid = get_business_id_for_user(current_user, business_id)
    templates = _get_templates_for_business(db, bid)
    # Also return available tokens for the UI
    return {"templates": templates, "tokens": TOKENS}


@router.put("/api/notification-templates")
def save_notification_templates(
    body: dict,
    business_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_user),
):
    """
    Upsert one or more templates.
    Expects body: { "templates": [{ "event_type", "channel", "subject", "body" }, ...] }
    """
    bid = get_business_id_for_user(current_user, business_id)
    incoming = body.get("templates", [])

    for item in incoming:
        event_type = item.get("event_type")
        channel = item.get("channel")
        if (event_type, channel) not in ALL_KEYS:
            continue

        existing = (
            db.query(NotificationTemplate)
            .filter(
                NotificationTemplate.business_id == bid,
                NotificationTemplate.event_type == event_type,
                NotificationTemplate.channel == channel,
            )
            .first()
        )

        if existing:
            if "subject" in item:
                existing.subject = item["subject"]
            if "body" in item:
                existing.body = item["body"]
            if "is_active" in item:
                existing.is_active = item["is_active"]
        else:
            db.add(NotificationTemplate(
                business_id=bid,
                event_type=event_type,
                channel=channel,
                subject=item.get("subject"),
                body=item.get("body", ""),
                is_active=item.get("is_active", True),
            ))

    db.commit()
    return {"templates": _get_templates_for_business(db, bid), "tokens": TOKENS}


@router.post("/api/notification-templates/reset")
def reset_notification_templates(
    business_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_user),
):
    """Delete all saved templates for a business, reverting to platform defaults."""
    bid = get_business_id_for_user(current_user, business_id)
    db.query(NotificationTemplate).filter(
        NotificationTemplate.business_id == bid
    ).delete()
    db.commit()
    return {"templates": _get_templates_for_business(db, bid), "tokens": TOKENS}
