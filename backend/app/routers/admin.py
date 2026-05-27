"""
Admin utility endpoints — manual triggers for background jobs and diagnostics.
All endpoints require a logged-in admin user.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.admin_user import AdminUser
from app.utils.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.post("/trigger/reminders")
def trigger_reminders(
    current_user: AdminUser = Depends(get_current_user),
):
    """
    Manually fire the next-day reminder job right now, bypassing the noon
    time window.  Useful for testing — reminders are still idempotent so
    re-triggering won't double-send.
    """
    from app.services.scheduler import _send_appointment_reminders
    _send_appointment_reminders(force=True)
    return {"status": "ok", "message": "Reminder job executed (force=True)"}


@router.post("/trigger/otw-prompts")
def trigger_otw_prompts(
    current_user: AdminUser = Depends(get_current_user),
):
    """
    Manually fire the OTW tech-prompt job right now.
    Only sends to appointments whose scheduled_start is 45–75 min away.
    """
    from app.services.scheduler import _send_otw_tech_prompts
    _send_otw_tech_prompts()
    return {"status": "ok", "message": "OTW tech-prompt job executed"}


@router.post("/trigger/morning-kickoffs")
def trigger_morning_kickoffs(
    current_user: AdminUser = Depends(get_current_user),
):
    """
    Manually fire the morning kickoff job right now.
    Only sends to technicians whose first appointment is within the next 60 min
    and it's past 07:00 in the business's local timezone.
    """
    from app.services.scheduler import _send_otw_morning_kickoffs
    _send_otw_morning_kickoffs()
    return {"status": "ok", "message": "Morning kickoff job executed"}


# ---------------------------------------------------------------------------
# Per-appointment notification triggers
# ---------------------------------------------------------------------------

def _get_appointment_or_404(db: Session, appointment_id: int):
    from app.models.appointment import Appointment
    appt = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if not appt:
        raise HTTPException(status_code=404, detail="Appointment not found")
    return appt


@router.post("/appointments/{appointment_id}/resend-confirmation")
def resend_confirmation(
    appointment_id: int,
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_user),
):
    """Re-send the booking confirmation SMS + email to the customer."""
    from app.services.notifications import send_confirmation
    appt = _get_appointment_or_404(db, appointment_id)
    results = send_confirmation(db, appt)
    logger.info("Admin resend confirmation for appt %d: %s", appointment_id, results)
    return {"status": "ok", "results": results}


@router.post("/appointments/{appointment_id}/send-reminder")
def send_reminder_now(
    appointment_id: int,
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_user),
):
    """Send a 24h-style reminder SMS + email for this appointment right now."""
    from app.services.notifications import send_reminder
    appt = _get_appointment_or_404(db, appointment_id)
    results = send_reminder(db, appt)
    logger.info("Admin send reminder for appt %d: %s", appointment_id, results)
    return {"status": "ok", "results": results}


@router.post("/appointments/{appointment_id}/send-review-request")
def send_review_request_now(
    appointment_id: int,
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_user),
):
    """Manually send a review request SMS + email for a completed appointment."""
    from app.services.notifications import send_review_request
    appt = _get_appointment_or_404(db, appointment_id)
    results = send_review_request(db, appt)
    logger.info("Admin send review request for appt %d: %s", appointment_id, results)
    return {"status": "ok", "results": results}


@router.get("/scheduler/status")
def scheduler_status(
    current_user: AdminUser = Depends(get_current_user),
):
    """Return the next scheduled run times for all background jobs."""
    from app.services.scheduler import _scheduler
    if not _scheduler or not _scheduler.running:
        return {"running": False, "jobs": []}

    jobs = []
    for job in _scheduler.get_jobs():
        jobs.append({
            "id": job.id,
            "name": job.name,
            "next_run": job.next_run_time.isoformat() if job.next_run_time else None,
        })
    return {"running": True, "jobs": jobs}
