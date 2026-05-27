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


def _send_appointment_reminders(force: bool = False):
    """
    Hourly job: around noon in each business's local timezone, send reminders for
    all confirmed appointments on the NEXT OPEN business day.
    Pass force=True to bypass the noon window check (used by the admin test endpoint).

    "Next open day" = the nearest future date (starting from tomorrow) that has
    a business_hours row with is_open=True.  This means:
      - Mon–Thu noon  → reminds about the following day
      - Fri noon      → if Sat/Sun are closed, reminds about Monday
      - Any day before a long closure → jumps to the next open day (up to 4 days)

    Idempotent — skips appointments that already have a reminder_24h log entry.
    Late-night-safe — only fires between 11:00 and 13:00 in the business's
    local timezone, so customers never receive messages at odd hours.
    """
    import pytz
    from datetime import date as date_type, time as time_type
    from app.database import SessionLocal
    from app.models.appointment import Appointment
    from app.models.business import Business
    from app.models.business_hours import BusinessHours
    from app.models.notification import NotificationLog
    from app.services.notifications import send_reminder

    db = SessionLocal()
    try:
        now_utc = datetime.now(timezone.utc)
        businesses = db.query(Business).filter(Business.is_active == True).all()

        sent_count = 0
        for business in businesses:
            # Resolve the business's local timezone
            biz_tz_str = getattr(business, "timezone", None) or "America/New_York"
            try:
                biz_tz = pytz.timezone(biz_tz_str)
            except Exception:
                biz_tz = pytz.utc

            now_local = now_utc.astimezone(biz_tz)

            # Only fire the reminder logic between 11:00 and 13:00 local time
            # (catches the noon run even if server clock drifts slightly)
            # force=True bypasses this check for manual admin triggers
            if not force and not (11 <= now_local.hour < 13):
                continue

            # Find the next open day: scan tomorrow onward, up to 4 days ahead
            target_date = None
            for days_ahead in range(1, 5):
                candidate = (now_local + timedelta(days=days_ahead)).date()
                weekday = candidate.weekday()  # 0=Monday … 6=Sunday
                has_hours = (
                    db.query(BusinessHours)
                    .filter(
                        BusinessHours.business_id == business.id,
                        BusinessHours.day_of_week == weekday,
                        BusinessHours.is_active == True,
                    )
                    .first()
                )
                if has_hours:
                    target_date = candidate
                    break

            if target_date is None:
                logger.info(
                    "Reminder job: no open day found in next 4 days for business %d — skipping",
                    business.id,
                )
                continue

            # Build UTC bounds for the entire target date in the business's timezone
            day_start_utc = biz_tz.localize(
                datetime.combine(target_date, time_type.min)
            ).astimezone(timezone.utc)
            day_end_utc = biz_tz.localize(
                datetime.combine(target_date, time_type.max)
            ).astimezone(timezone.utc)

            upcoming = (
                db.query(Appointment)
                .filter(
                    Appointment.business_id == business.id,
                    Appointment.scheduled_start >= day_start_utc,
                    Appointment.scheduled_start <= day_end_utc,
                    Appointment.status.notin_(["cancelled", "completed"]),
                )
                .all()
            )

            for appt in upcoming:
                # Skip if we already sent a reminder for this appointment
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
                    "Reminder sent for appt %d (target: %s) — SMS: %s, Email: %s",
                    appt.id, target_date, results.get("sms"), results.get("email"),
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

            # Skip if a morning kickoff was already sent for this appointment —
            # the kickoff already asked the tech to reply YES for their first stop.
            kickoff_sent = (
                db.query(NotificationLog)
                .filter(
                    NotificationLog.appointment_id == appt.id,
                    NotificationLog.event == "otw_morning_kickoff",
                    NotificationLog.status == "sent",
                )
                .first()
            )
            if kickoff_sent:
                logger.info(
                    "OTW job: skipping appt %d — morning kickoff already sent",
                    appt.id,
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


def _send_otw_morning_kickoffs():
    """
    Every 15 minutes: for each technician whose first appointment today starts
    within the next 60 minutes, send a morning kickoff SMS — but NEVER before
    07:00 in the business's local timezone.

    The kickoff replaces the standard otw_tech_prompt for the first stop of the
    day. The scheduler job that sends otw_tech_prompt will skip the first
    appointment if a morning kickoff has already been sent for it.

    Idempotent — checks notification_logs for an existing otw_morning_kickoff
    entry before sending.
    """
    import pytz
    from app.database import SessionLocal
    from app.models.appointment import Appointment
    from app.models.business import Business
    from app.models.notification import NotificationLog
    from app.services.notifications import send_otw_morning_kickoff

    db = SessionLocal()
    try:
        now_utc = datetime.now(timezone.utc)
        window_end = now_utc + timedelta(minutes=60)
        today_utc_start = now_utc.replace(hour=0, minute=0, second=0, microsecond=0)
        today_utc_end   = today_utc_start + timedelta(days=1)

        # Find all active businesses
        businesses = db.query(Business).filter(Business.is_active == True).all()

        sent_count = 0
        for business in businesses:
            # Determine local time for this business using its timezone (default UTC)
            biz_tz_str = getattr(business, "timezone", None) or "America/New_York"
            try:
                biz_tz = pytz.timezone(biz_tz_str)
            except Exception:
                biz_tz = pytz.utc

            now_local = now_utc.astimezone(biz_tz)

            # Do not send kickoffs before 07:00 local business time
            if now_local.hour < 7:
                continue

            # Find techs with appointments today for this business
            todays_appts = (
                db.query(Appointment)
                .filter(
                    Appointment.business_id == business.id,
                    Appointment.scheduled_start >= today_utc_start,
                    Appointment.scheduled_start < today_utc_end,
                    Appointment.technician_id.isnot(None),
                    Appointment.status.notin_(["cancelled", "completed"]),
                )
                .order_by(Appointment.technician_id, Appointment.scheduled_start)
                .all()
            )

            # Group by technician
            tech_appts: dict[int, list] = {}
            for appt in todays_appts:
                tech_appts.setdefault(appt.technician_id, []).append(appt)

            for tech_id, appts in tech_appts.items():
                first_appt = appts[0]  # already sorted by scheduled_start

                # Only fire if first appointment is within the next 60 minutes
                if first_appt.scheduled_start > window_end:
                    continue

                # Skip if kickoff already sent for this appointment
                already_sent = (
                    db.query(NotificationLog)
                    .filter(
                        NotificationLog.appointment_id == first_appt.id,
                        NotificationLog.event == "otw_morning_kickoff",
                        NotificationLog.status == "sent",
                    )
                    .first()
                )
                if already_sent:
                    continue

                # Skip if tech is already en_route to this appointment
                if first_appt.status == "en_route":
                    continue

                tech = first_appt.technician
                appointment_count = len(appts)

                ok = send_otw_morning_kickoff(db, first_appt, tech, appointment_count)
                if ok:
                    sent_count += 1

        if sent_count:
            logger.info("Morning kickoff job: sent kickoffs to %d technicians", sent_count)

    except Exception as e:
        logger.error("Morning kickoff scheduler error: %s", e)
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

    # Every 30 minutes — send next-day reminders (fires during 11am–1pm local window)
    _scheduler.add_job(
        _send_appointment_reminders,
        trigger=IntervalTrigger(minutes=30),
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

    # Every 15 minutes — send morning kickoff SMS to techs ~1 hour before first stop
    _scheduler.add_job(
        _send_otw_morning_kickoffs,
        trigger=IntervalTrigger(minutes=15),
        id="send_otw_kickoffs",
        replace_existing=True,
    )

    _scheduler.start()
    logger.info(
        "Background scheduler started "
        "(recurring: daily 06:00 | reminders: every 30 min / noon-window | "
        "OTW prompts: every 15 min | morning kickoffs: every 15 min)"
    )


def stop_scheduler():
    """Gracefully stop the scheduler on app shutdown."""
    global _scheduler
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info("Background scheduler stopped")
