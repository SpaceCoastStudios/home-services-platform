"""Scheduling engine — availability calculation and appointment booking, scoped by business_id."""

from datetime import datetime, date, time, timedelta, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.config import settings
from app.models.appointment import Appointment
from app.models.blocked_time import BlockedTime
from app.models.business_hours import BusinessHours
from app.models.service_type import ServiceType
from app.models.system_settings import SystemSetting
from app.models.technician import Technician


def _get_setting(db: Session, business_id: int, key: str, default: int) -> int:
    """Get a system setting value for a business, falling back to config defaults."""
    setting = (
        db.query(SystemSetting)
        .filter(SystemSetting.key == key, SystemSetting.business_id == business_id)
        .first()
    )
    if setting:
        return int(setting.value)
    return default


def get_slot_granularity(db: Session, business_id: int) -> int:
    return _get_setting(db, business_id, "slot_granularity_minutes", settings.DEFAULT_SLOT_GRANULARITY_MINUTES)


def get_buffer_minutes(db: Session, business_id: int) -> int:
    return _get_setting(db, business_id, "buffer_minutes", settings.DEFAULT_BUFFER_MINUTES)


def get_max_advance_days(db: Session, business_id: int) -> int:
    return _get_setting(db, business_id, "max_advance_booking_days", settings.DEFAULT_MAX_ADVANCE_BOOKING_DAYS)


def get_min_lead_time_hours(db: Session, business_id: int) -> int:
    return _get_setting(db, business_id, "min_lead_time_hours", settings.DEFAULT_MIN_LEAD_TIME_HOURS)


def get_available_slots(
    db: Session,
    business_id: int,
    service_type_id: int,
    start_date: date,
    end_date: date,
    technician_id: Optional[int] = None,
) -> list[dict]:
    """
    Calculate available appointment slots for a service type across a date range,
    scoped to a specific business tenant.

    Returns a list of dicts per day:
    [
        {
            "date": "2026-04-01",
            "slots": [
                {"start": datetime, "end": datetime, "technician_ids": [1, 3]},
                ...
            ]
        },
        ...
    ]
    """
    # 1. Get service type for this business
    service = (
        db.query(ServiceType)
        .filter(ServiceType.id == service_type_id, ServiceType.business_id == business_id)
        .first()
    )
    if not service or not service.is_active:
        return []

    duration = timedelta(minutes=service.duration_minutes)
    granularity = timedelta(minutes=get_slot_granularity(db, business_id))
    buffer = timedelta(minutes=get_buffer_minutes(db, business_id))
    min_lead = timedelta(hours=get_min_lead_time_hours(db, business_id))

    # 2. Get business hours for this tenant
    all_hours = (
        db.query(BusinessHours)
        .filter(BusinessHours.business_id == business_id, BusinessHours.is_active == True)
        .all()
    )
    hours_by_day = {h.day_of_week: h for h in all_hours}

    # 3. Get qualified technicians for this business
    tech_query = (
        db.query(Technician)
        .filter(Technician.business_id == business_id, Technician.is_active == True)
    )
    if technician_id:
        tech_query = tech_query.filter(Technician.id == technician_id)
    technicians = tech_query.all()

    # Filter to techs with matching skills for the service category
    qualified_techs = [
        t for t in technicians if service.category in (t.skills or [])
    ]
    if not qualified_techs:
        return []

    # 4. Iterate each day in range
    results = []
    current_date = start_date
    now = datetime.now(timezone.utc)

    while current_date <= end_date:
        day_of_week = current_date.weekday()  # 0=Monday
        bh = hours_by_day.get(day_of_week)

        if not bh:
            current_date += timedelta(days=1)
            continue

        day_start = datetime.combine(current_date, bh.open_time, tzinfo=timezone.utc)
        day_end = datetime.combine(current_date, bh.close_time, tzinfo=timezone.utc)

        # Get business-wide blocked times for this tenant/day
        business_blocks = (
            db.query(BlockedTime)
            .filter(
                BlockedTime.business_id == business_id,
                BlockedTime.technician_id.is_(None),
                BlockedTime.start_datetime < day_end,
                BlockedTime.end_datetime > day_start,
            )
            .all()
        )

        # Generate candidate time slots
        slot_techs: dict[datetime, list[int]] = {}
        slot_time = day_start

        while slot_time + duration <= day_end:
            slot_end = slot_time + duration

            # Skip slots in the past or within min lead time
            if slot_time < now + min_lead:
                slot_time += granularity
                continue

            # Skip if overlaps a business-wide block
            business_blocked = any(
                block.start_datetime < slot_end and block.end_datetime > slot_time
                for block in business_blocks
            )
            if business_blocked:
                slot_time += granularity
                continue

            # Check each qualified technician
            available_tech_ids = []
            for tech in qualified_techs:
                # Check tech-specific blocked times
                tech_blocks = (
                    db.query(BlockedTime)
                    .filter(
                        BlockedTime.business_id == business_id,
                        BlockedTime.technician_id == tech.id,
                        BlockedTime.start_datetime < slot_end,
                        BlockedTime.end_datetime > slot_time,
                    )
                    .count()
                )
                if tech_blocks > 0:
                    continue

                # Check existing appointments (with buffer), scoped to this business
                buffered_start = slot_time - buffer
                buffered_end = slot_end + buffer
                conflicts = (
                    db.query(Appointment)
                    .filter(
                        Appointment.business_id == business_id,
                        Appointment.technician_id == tech.id,
                        Appointment.status.notin_(["cancelled", "no_show"]),
                        Appointment.scheduled_start < buffered_end,
                        Appointment.scheduled_end > buffered_start,
                    )
                    .count()
                )
                if conflicts == 0:
                    available_tech_ids.append(tech.id)

            if available_tech_ids:
                slot_techs[slot_time] = available_tech_ids

            slot_time += granularity

        # Build day result
        if slot_techs:
            slots = [
                {
                    "start": st,
                    "end": st + duration,
                    "technician_ids": tech_ids,
                }
                for st, tech_ids in sorted(slot_techs.items())
            ]
            results.append({"date": current_date.isoformat(), "slots": slots})

        current_date += timedelta(days=1)

    return results


def auto_assign_technician(
    db: Session,
    business_id: int,
    service_type_id: int,
    scheduled_start: datetime,
    scheduled_end: datetime,
    preferred_technician_id: Optional[int] = None,
) -> Optional[int]:
    """Pick the best available technician for a slot. Returns tech ID or None."""
    service = (
        db.query(ServiceType)
        .filter(ServiceType.id == service_type_id, ServiceType.business_id == business_id)
        .first()
    )
    if not service:
        return None

    buffer = timedelta(minutes=get_buffer_minutes(db, business_id))

    if preferred_technician_id:
        # Verify the preferred tech belongs to this business and is available
        tech = (
            db.query(Technician)
            .filter(Technician.id == preferred_technician_id, Technician.business_id == business_id)
            .first()
        )
        if tech and tech.is_active and service.category in (tech.skills or []):
            conflicts = (
                db.query(Appointment)
                .filter(
                    Appointment.business_id == business_id,
                    Appointment.technician_id == tech.id,
                    Appointment.status.notin_(["cancelled", "no_show"]),
                    Appointment.scheduled_start < scheduled_end + buffer,
                    Appointment.scheduled_end > scheduled_start - buffer,
                )
                .count()
            )
            if conflicts == 0:
                return tech.id

    # Auto-assign: find the tech with the fewest appointments that day
    techs = (
        db.query(Technician)
        .filter(Technician.business_id == business_id, Technician.is_active == True)
        .all()
    )
    qualified = [t for t in techs if service.category in (t.skills or [])]

    best_tech_id = None
    min_appointments = float("inf")

    for tech in qualified:
        # Check for conflicts
        conflicts = (
            db.query(Appointment)
            .filter(
                Appointment.business_id == business_id,
                Appointment.technician_id == tech.id,
                Appointment.status.notin_(["cancelled", "no_show"]),
                Appointment.scheduled_start < scheduled_end + buffer,
                Appointment.scheduled_end > scheduled_start - buffer,
            )
            .count()
        )
        if conflicts > 0:
            continue

        # Count existing appointments for the day (load balancing)
        day_start = datetime.combine(scheduled_start.date(), time.min, tzinfo=timezone.utc)
        day_end = datetime.combine(scheduled_start.date(), time.max, tzinfo=timezone.utc)
        day_count = (
            db.query(Appointment)
            .filter(
                Appointment.business_id == business_id,
                Appointment.technician_id == tech.id,
                Appointment.status.notin_(["cancelled", "no_show"]),
                Appointment.scheduled_start >= day_start,
                Appointment.scheduled_start < day_end,
            )
            .count()
        )
        if day_count < min_appointments:
            min_appointments = day_count
            best_tech_id = tech.id

    return best_tech_id
