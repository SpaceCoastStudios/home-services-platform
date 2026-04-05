"""Recurring schedule endpoints — create, manage, and generate appointments from patterns."""

from datetime import date, datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.admin_user import AdminUser
from app.models.appointment import Appointment
from app.models.recurring_schedule import RecurringSchedule
from app.models.service_type import ServiceType
from app.schemas.recurring_schedule import (
    RecurringScheduleCreate,
    RecurringScheduleUpdate,
    RecurringScheduleResponse,
)
from app.services.scheduling import auto_assign_technician
from app.utils.auth import get_current_user, get_business_id_for_user

router = APIRouter(prefix="/api/recurring", tags=["recurring"])


# ── Helpers ───────────────────────────────────────────────────────────────────

def _enrich(schedule: RecurringSchedule) -> RecurringScheduleResponse:
    resp = RecurringScheduleResponse.model_validate(schedule)
    if schedule.customer:
        resp.customer_name = schedule.customer.full_name
    if schedule.service_type:
        resp.service_name = schedule.service_type.name
    if schedule.technician:
        resp.technician_name = schedule.technician.name
    return resp


def _next_dates(schedule: RecurringSchedule, from_date: date, until_date: date) -> list[date]:
    """
    Return all occurrence dates for a recurring schedule between from_date and until_date.
    """
    dates: list[date] = []
    cursor = from_date

    if schedule.end_date:
        until_date = min(until_date, schedule.end_date)

    if cursor < schedule.start_date:
        cursor = schedule.start_date

    if schedule.frequency == "monthly":
        # Pin to preferred_day_of_month
        dom = schedule.preferred_day_of_month or 1
        # Start from the first valid month
        if cursor.day > dom:
            # Move to next month
            if cursor.month == 12:
                cursor = date(cursor.year + 1, 1, dom)
            else:
                cursor = date(cursor.year, cursor.month + 1, dom)
        else:
            cursor = date(cursor.year, cursor.month, dom)

        while cursor <= until_date:
            dates.append(cursor)
            # Advance one month
            if cursor.month == 12:
                cursor = date(cursor.year + 1, 1, dom)
            else:
                cursor = date(cursor.year, cursor.month + 1, dom)

    else:
        # weekly or biweekly — pin to preferred_day_of_week
        dow = schedule.preferred_day_of_week if schedule.preferred_day_of_week is not None else 0
        step = timedelta(weeks=1) if schedule.frequency == "weekly" else timedelta(weeks=2)

        # Advance cursor to the first matching weekday on or after cursor
        days_ahead = (dow - cursor.weekday()) % 7
        cursor = cursor + timedelta(days=days_ahead)

        while cursor <= until_date:
            dates.append(cursor)
            cursor += step

    return dates


def generate_appointments_for_schedule(
    db: Session,
    schedule: RecurringSchedule,
    lookahead_days: Optional[int] = None,
) -> list[Appointment]:
    """
    Generate (and persist) upcoming appointments for a recurring schedule.
    Skips dates that already have an appointment from this schedule.
    Returns the list of newly created appointments.
    """
    days_ahead = lookahead_days or schedule.lookahead_days
    today = date.today()
    until = today + timedelta(days=days_ahead)

    # Dates already booked for this schedule
    existing = db.query(Appointment).filter(
        Appointment.recurring_schedule_id == schedule.id,
        Appointment.status.notin_(["cancelled"]),
    ).all()
    existing_dates = {a.scheduled_start.date() for a in existing}

    service = db.query(ServiceType).filter(ServiceType.id == schedule.service_type_id).first()
    if not service:
        return []

    duration = timedelta(minutes=service.duration_minutes)
    new_appointments = []

    for occurrence_date in _next_dates(schedule, today, until):
        if occurrence_date in existing_dates:
            continue

        scheduled_start = datetime.combine(
            occurrence_date, schedule.preferred_time, tzinfo=timezone.utc
        )
        scheduled_end = scheduled_start + duration

        tech_id = auto_assign_technician(
            db,
            schedule.business_id,
            schedule.service_type_id,
            scheduled_start,
            scheduled_end,
            schedule.technician_id,
        )
        if tech_id is None:
            # No tech available for this slot — skip (admin can reschedule manually)
            continue

        appt = Appointment(
            business_id=schedule.business_id,
            customer_id=schedule.customer_id,
            technician_id=tech_id,
            service_type_id=schedule.service_type_id,
            recurring_schedule_id=schedule.id,
            scheduled_start=scheduled_start,
            scheduled_end=scheduled_end,
            status="confirmed",
            source="recurring",
            address=schedule.address,
            notes=schedule.notes,
        )
        db.add(appt)
        new_appointments.append(appt)

    db.commit()
    return new_appointments


# ── Routes ────────────────────────────────────────────────────────────────────

@router.get("", response_model=list[RecurringScheduleResponse])
def list_recurring_schedules(
    is_active: Optional[bool] = None,
    customer_id: Optional[int] = None,
    business_id: Optional[int] = Query(None),
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_user),
):
    bid = get_business_id_for_user(current_user, business_id)
    q = db.query(RecurringSchedule).filter(RecurringSchedule.business_id == bid)
    if is_active is not None:
        q = q.filter(RecurringSchedule.is_active == is_active)
    if customer_id:
        q = q.filter(RecurringSchedule.customer_id == customer_id)
    schedules = q.order_by(RecurringSchedule.created_at.desc()).offset(skip).limit(limit).all()
    return [_enrich(s) for s in schedules]


@router.get("/{schedule_id}", response_model=RecurringScheduleResponse)
def get_recurring_schedule(
    schedule_id: int,
    business_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_user),
):
    bid = get_business_id_for_user(current_user, business_id)
    schedule = (
        db.query(RecurringSchedule)
        .filter(RecurringSchedule.id == schedule_id, RecurringSchedule.business_id == bid)
        .first()
    )
    if not schedule:
        raise HTTPException(status_code=404, detail="Recurring schedule not found")
    return _enrich(schedule)


@router.post("", response_model=RecurringScheduleResponse, status_code=201)
def create_recurring_schedule(
    body: RecurringScheduleCreate,
    business_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_user),
):
    bid = get_business_id_for_user(current_user, business_id)

    # Validate service belongs to this business
    service = (
        db.query(ServiceType)
        .filter(ServiceType.id == body.service_type_id, ServiceType.business_id == bid)
        .first()
    )
    if not service:
        raise HTTPException(status_code=404, detail="Service type not found")

    # Validate frequency-specific fields
    if body.frequency in ("weekly", "biweekly") and body.preferred_day_of_week is None:
        raise HTTPException(
            status_code=422,
            detail="preferred_day_of_week is required for weekly/biweekly schedules",
        )
    if body.frequency == "monthly" and body.preferred_day_of_month is None:
        raise HTTPException(
            status_code=422,
            detail="preferred_day_of_month is required for monthly schedules",
        )

    schedule = RecurringSchedule(
        business_id=bid,
        **body.model_dump(),
    )
    db.add(schedule)
    db.commit()
    db.refresh(schedule)

    # Generate the first batch of appointments immediately
    generate_appointments_for_schedule(db, schedule)

    return _enrich(schedule)


@router.put("/{schedule_id}", response_model=RecurringScheduleResponse)
def update_recurring_schedule(
    schedule_id: int,
    body: RecurringScheduleUpdate,
    business_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_user),
):
    bid = get_business_id_for_user(current_user, business_id)
    schedule = (
        db.query(RecurringSchedule)
        .filter(RecurringSchedule.id == schedule_id, RecurringSchedule.business_id == bid)
        .first()
    )
    if not schedule:
        raise HTTPException(status_code=404, detail="Recurring schedule not found")

    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(schedule, field, value)

    db.commit()
    db.refresh(schedule)
    return _enrich(schedule)


@router.delete("/{schedule_id}", status_code=204)
def deactivate_recurring_schedule(
    schedule_id: int,
    business_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_user),
):
    """Soft-delete: marks the schedule inactive. Does not cancel future appointments."""
    bid = get_business_id_for_user(current_user, business_id)
    schedule = (
        db.query(RecurringSchedule)
        .filter(RecurringSchedule.id == schedule_id, RecurringSchedule.business_id == bid)
        .first()
    )
    if not schedule:
        raise HTTPException(status_code=404, detail="Recurring schedule not found")
    schedule.is_active = False
    db.commit()


@router.post("/{schedule_id}/generate", status_code=200)
def manually_generate_appointments(
    schedule_id: int,
    lookahead_days: int = Query(30, ge=1, le=365),
    business_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_user),
):
    """Manually trigger appointment generation for a schedule."""
    bid = get_business_id_for_user(current_user, business_id)
    schedule = (
        db.query(RecurringSchedule)
        .filter(RecurringSchedule.id == schedule_id, RecurringSchedule.business_id == bid)
        .first()
    )
    if not schedule:
        raise HTTPException(status_code=404, detail="Recurring schedule not found")
    if not schedule.is_active:
        raise HTTPException(status_code=400, detail="Schedule is inactive")

    new_appts = generate_appointments_for_schedule(db, schedule, lookahead_days)
    return {"generated": len(new_appts), "schedule_id": schedule_id}
