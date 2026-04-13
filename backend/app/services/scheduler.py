"""APScheduler background jobs — runs inside the FastAPI process."""

import logging
from datetime import datetime, timedelta, timezone
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

logger = logging.getLogger(__name__)

_scheduler: BackgroundScheduler | None = None


def _generate_recurring_appointments():
    """Daily job: generate upcoming appointments for all active recurring schedules."""
    # Import here to avoid circular imports at module load time
    from app.database import SessionLocal
    from app.models.recurring_schedule import RecurringSchedule
    from app.routers.recurring import generate_appointments_for_schedule

    db = SessionLocal()
    try:
        schedules = (
            db.query(RecurringSchedule)
            .filter(RecurringSchedule.is_active == True)
            .all()
        )
        total_generated = 0
        for schedule in schedules:
            new_appts = generate_appointments_for_schedule(db, schedule)
            total_generated += len(new_appts)

        if total_generated:
            logger.info(
                "Recurring scheduler: generated %d appointments across %d schedules",
                total_generated,
                len(schedules),
            )
    except Exception as e:
        logger.error("Recurring scheduler error: %s", e)
    finally:
        db.close()


def _send_appointment_reminders():
    """
    Hourly job: send 24-hour reminder to any customer whose appointment falls
    in the 23h–25h window from now.  Idempotent — skips appointments that
    already have a reminder_24h log entry.
    """
    from app.database import SessionLocal
    from app.models.appointment import Appointment
    from app.models.notification import NotificationLog
    from app.services.notifications import send_reminder

    db = SessionLocal()
    try:
        now = datetime.now(timezone.utc)
        window_start = now + timedelta(hours=23)
        window_end   = now + timedelta(hours=25)

        # Appointments in the 24h window that aren't cancelled
        upcoming = (
            db.query(Appointment)
            .filter(
                Appointment.scheduled_start >= window_start,
                Appointment.scheduled_start <= window_end,
                Appointment.status.notin_(["cancelled", "completed"]),
            )
            .all()
        )

        sent_count = 0
        for appt in upcoming:
            # Skip if we already sent a 24h reminder for this appointment
            already_sent = (
                db.query(NotificationLog)
                .filter(
                    NotificationLog.appointment_id == appt.id,
                    NotificationLog.event == "reminder_24h",
                    NotificationLog.status == "sent",
                )
                .first()
            )
            if already_sent:
                continue

            results = send_reminder(db, appt)
            logger.info(
                "Reminder sent for appt %d — SMS: %s, Email: %s",
                appt.id, results.get("sms"), results.get("email"),
            )
            sent_count += 1

        if sent_count:
            logger.info("Reminder job: sent reminders for %d appointments", sent_count)

    except Exception as e:
        logger.error("Reminder scheduler error: %s", e)
    finally:
        db.close()


def _send_otw_tech_prompts():
    """
    Every 15 minutes: find appointments starting in 45–75 minutes that have an
    assigned technician and haven't had an OTW prompt sent yet.  Text the tech:
    "Heading to <Customer> at <Address>. Reply YES when you're on the way."
    """
    from app.database import SessionLocal
    from app.models.appointment import Appointment
    from app.models.notification import NotificationLog
    from app.services.notifications import send_otw_tech_prompt

    db = SessionLocal()
    try:
        now = datetime.now(timezone.utc)
        window_start = now + timedelta(minutes=45)
        window_end   = now + timedelta(minutes=75)

        upcoming = (
            db.query(Appointment)
            .filter(
                Appointment.scheduled_start >= window_start,
                Appointment.scheduled_start <= window_end,
                Appointment.technician_id.isnot(None),
                Appointment.status.notin_(["cancelled", "completed", "en_route"]),
            )
            .all()
        )

        sent_count = 0
        for appt in upcoming:
            # Skip if we already sent an OTW prompt for this appointment
            already_sent = (
                db.query(NotificationLog)
                .filter(
                    NotificationLog.appointment_id == appt.id,
                    NotificationLog.event == "otw_tech_prompt",
                    NotificationLog.status == "sent",
                )
                .first()
            )
            if already_sent:
                continue

            # Skip if this tech already has a different en_route appointment —
            # we don't want two pending YES requests in the same thread.
            # The completion of the current job will trigger the next OTW prompt.
            if appt.technician_id:
                active_en_route = (
                    db.query(Appointment)
                    .filter(
                        Appointment.technician_id == appt.technician_id,
                        Appointment.id != appt.id,
                        Appointment.status == "en_route",
                    )
                    .first()
                )
                if active_en_route:
                    logger.info(
                        "OTW job: skipping appt %d — tech %d has appt %d still en_route",
                        appt.id, appt.technician_id, active_en_route.id,
                    )
                    continue

            ok = send_otw_tech_prompt(db, appt)
            if ok:
                sent_count += 1

        if sent_count:
            logger.info("OTW job: prompted %d technicians", sent_count)

    except Exception as e:
        logger.error("OTW scheduler error: %s", e)
    finally:
        db.close()


def start_scheduler():
    """Start the background scheduler. Call once at app startup."""
    global _scheduler
    if _scheduler and _scheduler.running:
        return

    _scheduler = BackgroundScheduler()

    # Daily at 06:00 — pre-generate recurring appointments
    _scheduler.add_job(
        _generate_recurring_appointments,
        trigger=CronTrigger(hour=6, minute=0),
        id="generate_recurring",
        replace_existing=True,
    )

    # Every hour — send 24h reminders for upcoming appointments
    _scheduler.add_job(
        _send_appointment_reminders,
        trigger=IntervalTrigger(hours=1),
        id="send_reminders",
        replace_existing=True,
    )

    # Every 15 minutes — send OTW tech prompts for appointments starting in ~1 hour
    _scheduler.add_job(
        _send_otw_tech_prompts,
        trigger=IntervalTrigger(minutes=15),
        id="send_otw_prompts",
        replace_existing=True,
    )

    _scheduler.start()
    logger.info(
        "Background scheduler started "
        "(recurring: daily 06:00 | reminders: hourly | OTW prompts: every 15 min)"
    )


def stop_scheduler():
    """Gracefully stop the scheduler on app shutdown."""
    global _scheduler
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info("Background scheduler stopped")
