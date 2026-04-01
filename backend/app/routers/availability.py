"""Availability and appointment endpoints — scoped by business_id."""

from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.models.admin_user import AdminUser
from app.models.appointment import Appointment
from app.models.service_type import ServiceType
from app.schemas.appointment import (
    AppointmentCreate,
    AppointmentUpdate,
    AppointmentResponse,
)
from app.services.scheduling import get_available_slots, auto_assign_technician
from app.utils.auth import get_current_user, get_business_id_for_user

router = APIRouter(tags=["scheduling"])


# --- Availability ---

@router.get("/api/availability")
def check_availability(
    service_type_id: int,
    start_date: str,  # ISO date string
    end_date: str,
    business_id: Optional[int] = Query(None, description="Business ID"),
    technician_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_user),
):
    """Get available appointment slots for a service type in a date range."""
    from datetime import date as date_type

    bid = get_business_id_for_user(current_user, business_id)

    try:
        sd = date_type.fromisoformat(start_date)
        ed = date_type.fromisoformat(end_date)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD.")

    results = get_available_slots(db, bid, service_type_id, sd, ed, technician_id)
    return {"service_type_id": service_type_id, "business_id": bid, "availability": results}


# --- Appointments (admin) ---

@router.get("/api/appointments", response_model=list[AppointmentResponse])
def list_appointments(
    status: Optional[str] = None,
    technician_id: Optional[int] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    business_id: Optional[int] = Query(None),
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_user),
):
    bid = get_business_id_for_user(current_user, business_id)
    query = db.query(Appointment).filter(Appointment.business_id == bid)

    if status:
        query = query.filter(Appointment.status == status)
    if technician_id:
        query = query.filter(Appointment.technician_id == technician_id)
    if start_date:
        from datetime import date as date_type, datetime, time, timezone
        sd = date_type.fromisoformat(start_date)
        query = query.filter(Appointment.scheduled_start >= datetime.combine(sd, time.min, tzinfo=timezone.utc))
    if end_date:
        from datetime import date as date_type, datetime, time, timezone
        ed = date_type.fromisoformat(end_date)
        query = query.filter(Appointment.scheduled_start <= datetime.combine(ed, time.max, tzinfo=timezone.utc))

    appointments = query.order_by(Appointment.scheduled_start.desc()).offset(skip).limit(limit).all()

    results = []
    for appt in appointments:
        resp = AppointmentResponse.model_validate(appt)
        resp.customer_name = appt.customer.full_name if appt.customer else None
        resp.technician_name = appt.technician.name if appt.technician else None
        resp.service_name = appt.service_type.name if appt.service_type else None
        results.append(resp)
    return results


@router.get("/api/appointments/{appointment_id}", response_model=AppointmentResponse)
def get_appointment(
    appointment_id: int,
    business_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_user),
):
    bid = get_business_id_for_user(current_user, business_id)
    appt = (
        db.query(Appointment)
        .filter(Appointment.id == appointment_id, Appointment.business_id == bid)
        .first()
    )
    if not appt:
        raise HTTPException(status_code=404, detail="Appointment not found")

    resp = AppointmentResponse.model_validate(appt)
    resp.customer_name = appt.customer.full_name if appt.customer else None
    resp.technician_name = appt.technician.name if appt.technician else None
    resp.service_name = appt.service_type.name if appt.service_type else None
    return resp


@router.post("/api/appointments", response_model=AppointmentResponse, status_code=201)
def create_appointment(
    body: AppointmentCreate,
    business_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_user),
):
    bid = get_business_id_for_user(current_user, business_id)

    # Verify service belongs to this business
    service = (
        db.query(ServiceType)
        .filter(ServiceType.id == body.service_type_id, ServiceType.business_id == bid)
        .first()
    )
    if not service:
        raise HTTPException(status_code=404, detail="Service type not found")

    scheduled_end = body.scheduled_start + timedelta(minutes=service.duration_minutes)

    # Auto-assign technician scoped to this business
    tech_id = auto_assign_technician(
        db, bid, body.service_type_id, body.scheduled_start, scheduled_end, body.technician_id
    )
    if tech_id is None:
        raise HTTPException(status_code=409, detail="No technician available for this time slot")

    appointment = Appointment(
        business_id=bid,
        customer_id=body.customer_id,
        technician_id=tech_id,
        service_type_id=body.service_type_id,
        scheduled_start=body.scheduled_start,
        scheduled_end=scheduled_end,
        status="confirmed",
        source=body.source,
        address=body.address,
        notes=body.notes,
    )
    db.add(appointment)
    db.commit()
    db.refresh(appointment)
    return appointment


@router.put("/api/appointments/{appointment_id}", response_model=AppointmentResponse)
def update_appointment(
    appointment_id: int,
    body: AppointmentUpdate,
    business_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_user),
):
    bid = get_business_id_for_user(current_user, business_id)
    appt = (
        db.query(Appointment)
        .filter(Appointment.id == appointment_id, Appointment.business_id == bid)
        .first()
    )
    if not appt:
        raise HTTPException(status_code=404, detail="Appointment not found")

    update_data = body.model_dump(exclude_unset=True)

    # If rescheduling, recalculate end time
    if "scheduled_start" in update_data:
        service = db.query(ServiceType).filter(ServiceType.id == appt.service_type_id).first()
        update_data["scheduled_end"] = update_data["scheduled_start"] + timedelta(
            minutes=service.duration_minutes
        )

    for field, value in update_data.items():
        setattr(appt, field, value)

    db.commit()
    db.refresh(appt)
    return appt


@router.post("/api/appointments/{appointment_id}/cancel", response_model=AppointmentResponse)
def cancel_appointment(
    appointment_id: int,
    business_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_user),
):
    bid = get_business_id_for_user(current_user, business_id)
    appt = (
        db.query(Appointment)
        .filter(Appointment.id == appointment_id, Appointment.business_id == bid)
        .first()
    )
    if not appt:
        raise HTTPException(status_code=404, detail="Appointment not found")
    if appt.status == "cancelled":
        raise HTTPException(status_code=400, detail="Appointment is already cancelled")

    appt.status = "cancelled"
    db.commit()
    db.refresh(appt)
    return appt
