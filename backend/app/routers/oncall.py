"""
On-call routing router.

Endpoints
---------
GET    /api/oncall/config              — get (or auto-create) on-call config
PUT    /api/oncall/config              — update config settings
GET    /api/oncall/rotation            — list rotation entries
POST   /api/oncall/rotation            — add a rotation entry
DELETE /api/oncall/rotation/{id}       — remove a rotation entry
GET    /api/oncall/override            — get active override (if any)
POST   /api/oncall/override            — set a manual override
DELETE /api/oncall/override            — clear active override
GET    /api/oncall/current             — who is on-call right now
POST   /api/oncall/webhook/voice       — Twilio TwiML webhook (unauthenticated)
"""

import logging
from datetime import datetime, timedelta, timezone, time as dt_time, date as dt_date
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.oncall import OnCallConfig, OnCallRotation, OnCallOverride
from app.models.technician import Technician
from app.routers.auth import get_current_user
from app.models.admin_user import AdminUser

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/oncall", tags=["oncall"])

DAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


# ── Schemas ────────────────────────────────────────────────────────────────────

class OnCallConfigUpdate(BaseModel):
    is_enabled: Optional[bool] = None
    after_hours_start: Optional[dt_time] = None
    after_hours_end: Optional[dt_time] = None
    emergency_window_enabled: Optional[bool] = None
    emergency_window_start: Optional[dt_time] = None
    emergency_window_end: Optional[dt_time] = None
    rotation_type: Optional[str] = None          # "day_of_week" | "weekly_rolling"
    rolling_start_date: Optional[dt_date] = None
    fallback_phone: Optional[str] = None
    fallback_name: Optional[str] = None


class RotationEntryCreate(BaseModel):
    technician_id: int
    day_of_week: Optional[int] = None    # 0-6 for day_of_week mode
    position: Optional[int] = None       # 0-indexed for weekly_rolling mode


class OverrideCreate(BaseModel):
    technician_id: int
    note: Optional[str] = None
    hours: int = 24                      # how long the override lasts (default 24h)


# ── Helpers ────────────────────────────────────────────────────────────────────

def _get_or_create_config(business_id: int, db: Session) -> OnCallConfig:
    """Return the on-call config for a business, creating a default one if absent."""
    config = db.query(OnCallConfig).filter(
        OnCallConfig.business_id == business_id
    ).first()
    if not config:
        config = OnCallConfig(business_id=business_id)
        db.add(config)
        db.commit()
        db.refresh(config)
    return config


def _get_active_override(config: OnCallConfig) -> Optional[OnCallOverride]:
    """Return the first non-expired override, or None."""
    now = datetime.now(timezone.utc)
    for override in config.overrides:
        exp = override.expires_at
        if exp.tzinfo is None:
            exp = exp.replace(tzinfo=timezone.utc)
        if exp > now:
            return override
    return None


def _current_on_call_technician(config: OnCallConfig, db: Session) -> Optional[Technician]:
    """
    Resolve who is on-call right now.

    Priority:
    1. Active manual override
    2. Rotation entry for today (day_of_week) or current week slot (weekly_rolling)
    3. None — caller should fall back to config.fallback_phone
    """
    # 1. Manual override
    override = _get_active_override(config)
    if override:
        return override.technician

    if not config.rotations:
        return None

    now_utc = datetime.now(timezone.utc)

    if config.rotation_type == "day_of_week":
        today_dow = now_utc.weekday()   # 0=Monday
        for entry in config.rotations:
            if entry.day_of_week == today_dow:
                return entry.technician

    elif config.rotation_type == "weekly_rolling":
        if not config.rolling_start_date:
            return None
        # How many full weeks since the reference Monday?
        ref = datetime(
            config.rolling_start_date.year,
            config.rolling_start_date.month,
            config.rolling_start_date.day,
            tzinfo=timezone.utc,
        )
        weeks_elapsed = (now_utc - ref).days // 7
        cycle_len = len(config.rotations)
        if cycle_len == 0:
            return None
        slot = weeks_elapsed % cycle_len
        # Find entry with matching position
        for entry in config.rotations:
            if entry.position == slot:
                return entry.technician

    return None


def _is_after_hours(config: OnCallConfig) -> bool:
    """Return True if the current UTC time falls within the configured after-hours window."""
    now_time = datetime.now(timezone.utc).time()
    start = config.after_hours_start
    end   = config.after_hours_end

    if start <= end:
        # Same-day window (rare for after-hours but handle it)
        return start <= now_time <= end
    else:
        # Overnight window (e.g. 18:00 → 08:00)
        return now_time >= start or now_time <= end


# ── Config endpoints ───────────────────────────────────────────────────────────

@router.get("/config")
def get_config(
    business_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_user),
):
    bid = business_id or current_user.business_id
    config = _get_or_create_config(bid, db)

    rotations = []
    for r in config.rotations:
        rotations.append({
            "id": r.id,
            "technician_id": r.technician_id,
            "technician_name": r.technician.name if r.technician else None,
            "day_of_week": r.day_of_week,
            "day_name": DAY_NAMES[r.day_of_week] if r.day_of_week is not None else None,
            "position": r.position,
        })

    active_override = _get_active_override(config)
    override_data = None
    if active_override:
        override_data = {
            "id": active_override.id,
            "technician_id": active_override.technician_id,
            "technician_name": active_override.technician.name,
            "note": active_override.note,
            "expires_at": active_override.expires_at.isoformat(),
        }

    return {
        "id": config.id,
        "business_id": config.business_id,
        "is_enabled": config.is_enabled,
        "after_hours_start": config.after_hours_start.strftime("%H:%M"),
        "after_hours_end": config.after_hours_end.strftime("%H:%M"),
        "emergency_window_enabled": config.emergency_window_enabled,
        "emergency_window_start": config.emergency_window_start.strftime("%H:%M") if config.emergency_window_start else None,
        "emergency_window_end": config.emergency_window_end.strftime("%H:%M") if config.emergency_window_end else None,
        "rotation_type": config.rotation_type,
        "rolling_start_date": config.rolling_start_date.isoformat() if config.rolling_start_date else None,
        "fallback_phone": config.fallback_phone,
        "fallback_name": config.fallback_name,
        "rotations": rotations,
        "active_override": override_data,
    }


@router.put("/config")
def update_config(
    payload: OnCallConfigUpdate,
    business_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_user),
):
    bid = business_id or current_user.business_id
    config = _get_or_create_config(bid, db)

    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(config, field, value)

    db.commit()
    db.refresh(config)
    return {"message": "On-call config updated"}


# ── Rotation endpoints ─────────────────────────────────────────────────────────

@router.post("/rotation", status_code=201)
def add_rotation_entry(
    payload: RotationEntryCreate,
    business_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_user),
):
    bid = business_id or current_user.business_id
    config = _get_or_create_config(bid, db)

    # Validate technician belongs to business
    tech = db.query(Technician).filter(
        Technician.id == payload.technician_id,
        Technician.business_id == bid,
    ).first()
    if not tech:
        raise HTTPException(status_code=404, detail="Technician not found")

    entry = OnCallRotation(
        config_id=config.id,
        technician_id=payload.technician_id,
        day_of_week=payload.day_of_week,
        position=payload.position,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return {"id": entry.id, "message": "Rotation entry added"}


@router.delete("/rotation/{entry_id}", status_code=200)
def delete_rotation_entry(
    entry_id: int,
    business_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_user),
):
    bid = business_id or current_user.business_id
    config = _get_or_create_config(bid, db)

    entry = db.query(OnCallRotation).filter(
        OnCallRotation.id == entry_id,
        OnCallRotation.config_id == config.id,
    ).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Rotation entry not found")

    db.delete(entry)
    db.commit()
    return {"message": "Rotation entry removed"}


# ── Override endpoints ─────────────────────────────────────────────────────────

@router.get("/override")
def get_override(
    business_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_user),
):
    bid = business_id or current_user.business_id
    config = _get_or_create_config(bid, db)
    override = _get_active_override(config)
    if not override:
        return {"active_override": None}
    return {
        "active_override": {
            "id": override.id,
            "technician_id": override.technician_id,
            "technician_name": override.technician.name,
            "note": override.note,
            "expires_at": override.expires_at.isoformat(),
        }
    }


@router.post("/override", status_code=201)
def set_override(
    payload: OverrideCreate,
    business_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_user),
):
    bid = business_id or current_user.business_id
    config = _get_or_create_config(bid, db)

    tech = db.query(Technician).filter(
        Technician.id == payload.technician_id,
        Technician.business_id == bid,
    ).first()
    if not tech:
        raise HTTPException(status_code=404, detail="Technician not found")

    expires = datetime.now(timezone.utc) + timedelta(hours=max(1, payload.hours))
    override = OnCallOverride(
        config_id=config.id,
        technician_id=payload.technician_id,
        note=payload.note,
        expires_at=expires,
    )
    db.add(override)
    db.commit()
    db.refresh(override)
    return {
        "id": override.id,
        "technician_name": tech.name,
        "expires_at": override.expires_at.isoformat(),
        "message": f"{tech.name} set as on-call until {override.expires_at.strftime('%b %-d at %-I:%M %p UTC')}",
    }


@router.delete("/override", status_code=200)
def clear_override(
    business_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_user),
):
    bid = business_id or current_user.business_id
    config = _get_or_create_config(bid, db)
    override = _get_active_override(config)
    if not override:
        return {"message": "No active override to clear"}
    db.delete(override)
    db.commit()
    return {"message": "Override cleared — rotation is now active"}


# ── Current on-call endpoint ───────────────────────────────────────────────────

@router.get("/current")
def get_current_oncall(
    business_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_user),
):
    bid = business_id or current_user.business_id
    config = _get_or_create_config(bid, db)

    if not config.is_enabled:
        return {"on_call": None, "reason": "On-call routing is disabled"}

    tech = _current_on_call_technician(config, db)
    after_hours = _is_after_hours(config)

    if tech:
        source = "override" if _get_active_override(config) else "rotation"
        return {
            "on_call": {
                "technician_id": tech.id,
                "name": tech.name,
                "phone": tech.phone,
            },
            "source": source,
            "after_hours": after_hours,
        }

    # Fallback
    if config.fallback_phone:
        return {
            "on_call": {
                "technician_id": None,
                "name": config.fallback_name or "Company Contact",
                "phone": config.fallback_phone,
            },
            "source": "fallback",
            "after_hours": after_hours,
        }

    return {"on_call": None, "reason": "No on-call technician or fallback configured"}


# ── Twilio TwiML Webhook ───────────────────────────────────────────────────────

@router.post("/webhook/voice", response_class=PlainTextResponse)
async def voice_webhook(
    request: Request,
    business_id: int = Query(..., description="Business ID — include in Twilio webhook URL"),
    db: Session = Depends(get_db),
):
    """
    Twilio calls this endpoint when someone dials the business's Twilio number.

    Configure your Twilio number's Voice webhook to:
        POST https://your-api.com/api/oncall/webhook/voice?business_id=<ID>

    During business hours  → connect to main business phone
    After hours            → connect to on-call technician
    No one available       → voicemail
    """
    config = db.query(OnCallConfig).filter(
        OnCallConfig.business_id == business_id
    ).first()

    # On-call not configured — play a generic voicemail
    if not config or not config.is_enabled:
        return PlainTextResponse(
            _twiml_voicemail("Thank you for calling. Our office is currently closed. "
                             "Please leave your name, number, and a brief message "
                             "and we will return your call as soon as possible."),
            media_type="application/xml",
        )

    after_hours = _is_after_hours(config)

    if not after_hours:
        # During business hours — forward to main business line
        from app.models.business import Business
        business = db.query(Business).filter(Business.id == business_id).first()
        main_phone = business.phone if business else None

        if main_phone:
            return PlainTextResponse(
                _twiml_dial(main_phone,
                            "Thank you for calling. Please hold while we connect your call."),
                media_type="application/xml",
            )
        # No main phone on file — fall through to voicemail
        return PlainTextResponse(
            _twiml_voicemail("Thank you for calling. Please leave a message "
                             "and we will get back to you shortly."),
            media_type="application/xml",
        )

    # After hours — find on-call tech
    tech = _current_on_call_technician(config, db)
    forward_to = tech.phone if tech else config.fallback_phone
    forward_name = tech.name if tech else (config.fallback_name or "our on-call contact")

    if forward_to:
        logger.info(
            "Routing after-hours call for business %d to %s (%s)",
            business_id, forward_name, forward_to,
        )
        return PlainTextResponse(
            _twiml_dial(
                forward_to,
                f"Thank you for calling. This is an after-hours call. "
                f"Please hold while we connect you to {forward_name}.",
            ),
            media_type="application/xml",
        )

    # No one available — voicemail
    return PlainTextResponse(
        _twiml_voicemail(
            "Thank you for calling. We're unable to connect your call at this time. "
            "Please leave your name, number, and message after the tone "
            "and we will call you back as soon as possible."
        ),
        media_type="application/xml",
    )


# ── TwiML builders ────────────────────────────────────────────────────────────

def _twiml_dial(to_number: str, greeting: str) -> str:
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Say voice="Polly.Joanna">{greeting}</Say>
  <Dial timeout="30" action="/api/oncall/webhook/no-answer?business_id=0">
    <Number>{to_number}</Number>
  </Dial>
</Response>"""


def _twiml_voicemail(message: str) -> str:
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Say voice="Polly.Joanna">{message}</Say>
  <Record maxLength="120" transcribe="true" />
</Response>"""
