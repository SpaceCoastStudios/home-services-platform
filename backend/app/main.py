"""FastAPI application entry point."""

import logging

# Use the OS/Windows certificate store so HTTPS works behind antivirus SSL inspection.
try:
    import truststore
    truststore.inject_into_ssl()
except ImportError:
    pass  # Not installed — fine in production Linux environments
from contextlib import asynccontextmanager
from datetime import time

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from sqlalchemy import text
from app.config import settings
from app.database import init_db, SessionLocal
from app.models.admin_user import AdminUser
from app.models.business import Business
from app.models.business_hours import BusinessHours
from app.models.system_settings import SystemSetting
from app.utils.auth import hash_password

# Routers
from app.routers import (
    auth,
    customers,
    services,
    technicians,
    availability,
    business_hours,
    contact,
    calendar_links,
    businesses,
    recurring,
)
from app.services.scheduler import start_scheduler, stop_scheduler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def seed_defaults(db):
    """Seed default data on first run."""

    # --- Default Business Tenant ---
    # The platform needs at least one business for the admin user to belong to.
    default_business = db.query(Business).filter(Business.slug == "default").first()
    if not default_business:
        default_business = Business(
            name="Space Coast Studios Demo",
            slug="default",
            industry="hvac",
            plan="full",
            is_active=True,
            is_demo=True,
            ai_agent_name="Scout",
            brand_color="#2563eb",
        )
        db.add(default_business)
        db.flush()  # Get the ID before committing
        logger.info("Created default demo business tenant")

    bid = default_business.id

    # --- Default Admin User ---
    if not db.query(AdminUser).first():
        admin = AdminUser(
            username="admin",
            password_hash=hash_password("admin123"),
            role="admin",
            business_id=None,  # NULL = platform admin (can access all tenants)
        )
        db.add(admin)
        logger.info("Created default platform admin user (admin / admin123)")

    # --- Default Business Hours for demo tenant ---
    if not db.query(BusinessHours).filter(BusinessHours.business_id == bid).first():
        for day in range(5):  # 0=Mon through 4=Fri
            db.add(BusinessHours(
                business_id=bid,
                day_of_week=day,
                open_time=time(8, 0),
                close_time=time(17, 0),
                is_active=True,
            ))
        # Saturday half day
        db.add(BusinessHours(
            business_id=bid,
            day_of_week=5,
            open_time=time(9, 0),
            close_time=time(13, 0),
            is_active=True,
        ))
        logger.info("Seeded default business hours (Mon-Fri 8-5, Sat 9-1)")

    # --- Default System Settings for demo tenant ---
    default_settings = [
        ("slot_granularity_minutes", str(settings.DEFAULT_SLOT_GRANULARITY_MINUTES),
         "Time slot increment in minutes for appointment scheduling"),
        ("buffer_minutes", str(settings.DEFAULT_BUFFER_MINUTES),
         "Buffer time between appointments in minutes"),
        ("max_advance_booking_days", str(settings.DEFAULT_MAX_ADVANCE_BOOKING_DAYS),
         "How far in advance customers can book (days)"),
        ("min_lead_time_hours", str(settings.DEFAULT_MIN_LEAD_TIME_HOURS),
         "Minimum hours before an appointment can be booked"),
        ("max_appointments_per_tech_per_day", str(settings.DEFAULT_MAX_APPOINTMENTS_PER_TECH_PER_DAY),
         "Maximum appointments per technician per day"),
        ("allow_same_day_booking", str(settings.DEFAULT_ALLOW_SAME_DAY_BOOKING).lower(),
         "Whether same-day appointments are allowed"),
    ]
    for key, value, desc in default_settings:
        exists = (
            db.query(SystemSetting)
            .filter(SystemSetting.business_id == bid, SystemSetting.key == key)
            .first()
        )
        if not exists:
            db.add(SystemSetting(business_id=bid, key=key, value=value, description=desc))

    db.commit()


def run_migrations(db):
    """Apply any schema changes not handled by create_all (additive only — never destructive)."""
    # Add recurring_schedule_id to appointments if it doesn't exist yet
    try:
        db.execute(text(
            "ALTER TABLE appointments ADD COLUMN recurring_schedule_id INTEGER "
            "REFERENCES recurring_schedules(id)"
        ))
        db.commit()
        logger.info("Migration: added recurring_schedule_id to appointments")
    except Exception:
        db.rollback()  # Column already exists — safe to ignore

    # Create notification_logs table if it doesn't exist yet
    try:
        db.execute(text("""
            CREATE TABLE IF NOT EXISTS notification_logs (
                id          SERIAL PRIMARY KEY,
                appointment_id INTEGER NOT NULL REFERENCES appointments(id),
                type        VARCHAR(10) NOT NULL,
                event       VARCHAR(30) NOT NULL,
                sent_at     TIMESTAMP NOT NULL DEFAULT NOW(),
                status      VARCHAR(20) NOT NULL
            )
        """))
        db.commit()
        logger.info("Migration: notification_logs table ready")
    except Exception as e:
        db.rollback()
        logger.warning("Migration notification_logs skipped: %s", e)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    logger.info("Starting %s v%s", settings.APP_NAME, settings.APP_VERSION)
    init_db()

    db = SessionLocal()
    try:
        run_migrations(db)
        seed_defaults(db)
    finally:
        db.close()

    start_scheduler()

    yield

    stop_scheduler()
    logger.info("Shutting down")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

# CORS — origins loaded from config so they work in both dev and production
_allowed_origins = [o.strip() for o in settings.ALLOWED_ORIGINS.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(auth.router)
app.include_router(businesses.router)   # Platform admin: manage tenants
app.include_router(customers.router)
app.include_router(services.router)
app.include_router(technicians.router)
app.include_router(availability.router)
app.include_router(business_hours.router)
app.include_router(contact.router)
app.include_router(calendar_links.router)
app.include_router(recurring.router)


@app.get("/")
def root():
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
    }


@app.get("/health")
def health():
    return {"status": "ok"}
