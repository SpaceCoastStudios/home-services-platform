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
    Every 15 minutes: send morning kickoff SMS to technicians.

    Two variants:
      1. Techs WITH appointments today: fire 2 hours before their first appointment
         (30-minute trigger window to avoid re-firing every run).  No time-of-day
         floor — even a 5 AM text is fine for a tech with a 7 AM first stop.
      2. Techs WITHOUT appointments today: fire once between 07:00 and 08:00 local
         time with a "no appointments today" message.

    Idempotent:
      - WITH appointments: checks notification_logs for otw_morning_kickoff keyed
        on the first appointment's ID.
      - WITHOUT appointments: checks notification_logs for otw_morning_kickoff
        keyed on technician_id, created today (appointment_id = NULL).

    The OTW tech prompt job skips the first appointment if a morning kickoff was
    already sent for it.
    """
    import pytz
    from app.database import SessionLocal
    from app.models.appointment import Appointment
    from app.models.business import Business
    from app.models.technician import Technician
    from app.models.notification import NotificationLog
    from app.services.notifications import (
        send_otw_morning_kickoff,
        send_otw_morning_no_appointments,
    )

    db = SessionLocal()
    try:
        now_utc = datetime.now(timezone.utc)
        today_utc_start = now_utc.replace(hour=0, minute=0, second=0, microsecond=0)
        today_utc_end   = today_utc_start + timedelta(days=1)

        # Trigger window for "WITH appointments" variant:
        # send when first appointment is between 1h45min and 2h15min away.
        two_hours_from_now       = now_utc + timedelta(hours=2)
        kickoff_window_start_utc = two_hours_from_now - timedelta(minutes=15)
        kickoff_window_end_utc   = two_hours_from_now + timedelta(minutes=15)

        businesses = db.query(Business).filter(Business.is_active == True).all()

        sent_count = 0
        for business in businesses:
            biz_tz_str = getattr(business, "timezone", None) or "America/New_York"
            try:
                biz_tz = pytz.timezone(biz_tz_str)
            except Exception:
                biz_tz = pytz.utc

            now_local = now_utc.astimezone(biz_tz)

            # Fetch ALL active techs for this business
            all_techs = (
                db.query(Technician)
                .filter(
                    Technician.business_id == business.id,
                    Technician.is_active == True,
                )
                .all()
            )

            # Fetch today's appointments for the whole business (all techs)
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

            # Group appointments by technician ID
            tech_appts: dict[int, list] = {}
            for appt in todays_appts:
                tech_appts.setdefault(appt.technician_id, []).append(appt)

            for tech in all_techs:
                if not tech.phone:
                    continue

                appts = tech_appts.get(tech.id, [])

                if appts:
                    # ── VARIANT 1: Tech has appointments ──────────────────────
                    first_appt = appts[0]

                    # Check trigger window: first appt must start ~2 hours from now
                    first_start = first_appt.scheduled_start
                    if first_start.tzinfo is None:
                        first_start = first_start.replace(tzinfo=timezone.utc)

                    if not (kickoff_window_start_utc <= first_start <= kickoff_window_end_utc):
                        # Also fire immediately if first appointment already started and
                        # we never sent a kickoff (catch-up for edge cases like late boot)
                        if first_start >= now_utc:
                            continue  # not in window yet, come back later

                    # Idempotency check: keyed on first appointment ID
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

                    if first_appt.status == "en_route":
                        continue

                    # Build public schedule URL for this tech
                    schedule_url = (
                        f"https://api.spacecoaststudios.com/schedule/tech/{tech.schedule_token}"
                        if tech.schedule_token else None
                    )

                    ok = send_otw_morning_kickoff(db, first_appt, tech, appts, schedule_url)
                    if ok:
                        sent_count += 1

                else:
                    # ── VARIANT 2: Tech has no appointments today ──────────────
                    # Only send between 07:00 and 08:00 local business time
                    if not (7 <= now_local.hour < 8):
                        continue

                    # Idempotency check: keyed on technician_id, today
                    already_sent = (
                        db.query(NotificationLog)
                        .filter(
                            NotificationLog.technician_id == tech.id,
                            NotificationLog.appointment_id.is_(None),
                            NotificationLog.event == "otw_morning_kickoff",
                            NotificationLog.status == "sent",
                            NotificationLog.sent_at >= today_utc_start,
                            NotificationLog.sent_at < today_utc_end,
                        )
                        .first()
                    )
                    if already_sent:
                        continue

                    ok = send_otw_morning_no_appointments(db, tech, business)
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
