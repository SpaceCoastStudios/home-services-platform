"""Business hours, blocked times, and system settings endpoints — scoped by business_id."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.models.admin_user import AdminUser
from app.models.business_hours import BusinessHours
from app.models.blocked_time import BlockedTime
from app.models.system_settings import SystemSetting
from app.schemas.business_hours import (
    BusinessHoursEntry,
    BusinessHoursUpdate,
    BusinessHoursResponse,
    BlockedTimeCreate,
    BlockedTimeResponse,
    SystemSettingResponse,
    SystemSettingUpdate,
)
from app.utils.auth import get_current_user, get_business_id_for_user

router = APIRouter(prefix="/api", tags=["settings"])


# --- Business Hours ---

@router.get("/business-hours", response_model=list[BusinessHoursResponse])
def get_business_hours(
    business_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_user),
):
    bid = get_business_id_for_user(current_user, business_id)
    return (
        db.query(BusinessHours)
        .filter(BusinessHours.business_id == bid)
        .order_by(BusinessHours.day_of_week)
        .all()
    )


@router.put("/business-hours", response_model=list[BusinessHoursResponse])
def update_business_hours(
    body: BusinessHoursUpdate,
    business_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_user),
):
    """Batch replace all business hours for this business."""
    bid = get_business_id_for_user(current_user, business_id)

    # Only delete hours belonging to this business
    db.query(BusinessHours).filter(BusinessHours.business_id == bid).delete()

    new_hours = []
    for entry in body.hours:
        bh = BusinessHours(**entry.model_dump(), business_id=bid)
        db.add(bh)
        new_hours.append(bh)
    db.commit()
    for h in new_hours:
        db.refresh(h)
    return new_hours


# --- Blocked Times ---

@router.get("/blocked-times", response_model=list[BlockedTimeResponse])
def list_blocked_times(
    business_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_user),
):
    bid = get_business_id_for_user(current_user, business_id)
    return (
        db.query(BlockedTime)
        .filter(BlockedTime.business_id == bid)
        .order_by(BlockedTime.start_datetime)
        .all()
    )


@router.post("/blocked-times", response_model=BlockedTimeResponse, status_code=201)
def create_blocked_time(
    body: BlockedTimeCreate,
    business_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_user),
):
    bid = get_business_id_for_user(current_user, business_id)
    blocked = BlockedTime(**body.model_dump(), business_id=bid)
    db.add(blocked)
    db.commit()
    db.refresh(blocked)
    return blocked


@router.delete("/blocked-times/{blocked_id}", status_code=204)
def delete_blocked_time(
    blocked_id: int,
    business_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_user),
):
    bid = get_business_id_for_user(current_user, business_id)
    blocked = (
        db.query(BlockedTime)
        .filter(BlockedTime.id == blocked_id, BlockedTime.business_id == bid)
        .first()
    )
    if not blocked:
        raise HTTPException(status_code=404, detail="Blocked time not found")
    db.delete(blocked)
    db.commit()


# --- System Settings ---
# System settings are global (platform-level), not per-business.
# Only platform admins or business admins scoped to their business can read/write them.

@router.get("/settings", response_model=list[SystemSettingResponse])
def get_settings(
    business_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_user),
):
    bid = get_business_id_for_user(current_user, business_id)
    return db.query(SystemSetting).filter(SystemSetting.business_id == bid).all()


@router.put("/settings/{key}", response_model=SystemSettingResponse)
def update_setting(
    key: str,
    body: SystemSettingUpdate,
    business_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_user),
):
    bid = get_business_id_for_user(current_user, business_id)
    setting = (
        db.query(SystemSetting)
        .filter(SystemSetting.key == key, SystemSetting.business_id == bid)
        .first()
    )
    if not setting:
        raise HTTPException(status_code=404, detail=f"Setting '{key}' not found")
    setting.value = body.value
    db.commit()
    db.refresh(setting)
    return setting
