"""Business (tenant) management — platform admin only."""

from datetime import datetime, time, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel

from app.config import settings
from app.database import get_db
from app.models.business import Business
from app.models.admin_user import AdminUser
from app.models.business_hours import BusinessHours
from app.models.system_settings import SystemSetting
from app.utils.auth import get_platform_admin, get_current_user, hash_password, create_access_token

router = APIRouter(prefix="/api/businesses", tags=["businesses"])


class BusinessCreate(BaseModel):
    name: str
    slug: str
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    website: Optional[str] = None
    industry: Optional[str] = None
    brand_color: Optional[str] = None
    plan: str = "full"
    is_demo: bool = False
    ai_agent_name: Optional[str] = None
    ai_system_prompt: Optional[str] = None
    from_email: Optional[str] = None
    # Optional: create an admin user for this business at the same time
    admin_username: Optional[str] = None
    admin_password: Optional[str] = None


class BusinessUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    website: Optional[str] = None
    industry: Optional[str] = None
    brand_color: Optional[str] = None
    logo_url: Optional[str] = None
    plan: Optional[str] = None
    is_active: Optional[bool] = None
    ai_agent_name: Optional[str] = None
    ai_system_prompt: Optional[str] = None
    twilio_phone_number: Optional[str] = None
    from_email: Optional[str] = None
    ai_response_mode: Optional[str] = None
    google_review_url: Optional[str] = None
    twilio_phone_number: Optional[str] = None
    timezone: Optional[str] = None
    route_optimization_enabled: Optional[bool] = None
    has_completed_setup: Optional[bool] = None


class BusinessResponse(BaseModel):
    id: int
    name: str
    slug: str
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    website: Optional[str] = None
    industry: Optional[str] = None
    brand_color: Optional[str] = None
    logo_url: Optional[str] = None
    plan: str
    is_active: bool
    is_demo: bool
    ai_agent_name: Optional[str] = None
    ai_system_prompt: Optional[str] = None
    from_email: Optional[str] = None
    ai_response_mode: Optional[str] = None
    google_review_url: Optional[str] = None
    timezone: Optional[str] = None
    route_optimization_enabled: bool = False
    has_completed_setup: bool = False
    stripe_customer_id: Optional[str] = None
    stripe_subscription_id: Optional[str] = None
    subscription_tier: Optional[str] = None
    subscription_status: Optional[str] = None
    subscription_period_end: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}


@router.get("/me", response_model=BusinessResponse)
def get_my_business(
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_user),
):
    """
    Return the authenticated user's own business.
    Used by business admins to fetch their full business record
    (e.g. during the first-login setup wizard).
    """
    if current_user.is_platform_admin or not current_user.business_id:
        raise HTTPException(
            status_code=400,
            detail="Platform admins don't have a single business. Use /api/businesses/{id} instead.",
        )
    b = db.query(Business).filter(Business.id == current_user.business_id).first()
    if not b:
        raise HTTPException(status_code=404, detail="Business not found")
    return b


@router.get("", response_model=list[BusinessResponse])
def list_businesses(
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_platform_admin),
):
    return db.query(Business).order_by(Business.name).all()


@router.post("", response_model=BusinessResponse, status_code=201)
def create_business(
    body: BusinessCreate,
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_platform_admin),
):
    # Check slug uniqueness
    if db.query(Business).filter(Business.slug == body.slug).first():
        raise HTTPException(status_code=409, detail="Slug already in use")

    business = Business(
        name=body.name,
        slug=body.slug,
        phone=body.phone,
        email=body.email,
        address=body.address,
        website=body.website,
        industry=body.industry,
        brand_color=body.brand_color,
        plan=body.plan,
        is_demo=body.is_demo,
        ai_agent_name=body.ai_agent_name,
        ai_system_prompt=body.ai_system_prompt,
        from_email=body.from_email,
    )
    db.add(business)
    db.flush()  # get the ID before committing

    # Optionally create an admin user for this business
    if body.admin_username and body.admin_password:
        admin = AdminUser(
            business_id=business.id,
            username=body.admin_username,
            password_hash=hash_password(body.admin_password),
            role="admin",
        )
        db.add(admin)

    # Seed default business hours (Mon-Fri 8-5, Sat 9-1)
    for day in range(5):
        db.add(BusinessHours(
            business_id=business.id,
            day_of_week=day,
            open_time=time(8, 0),
            close_time=time(17, 0),
            is_active=True,
        ))
    db.add(BusinessHours(
        business_id=business.id,
        day_of_week=5,
        open_time=time(9, 0),
        close_time=time(13, 0),
        is_active=True,
    ))

    # Seed default system settings
    default_settings = [
        ("slot_granularity_minutes", str(settings.DEFAULT_SLOT_GRANULARITY_MINUTES),
         "Time slot increment in minutes"),
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
        db.add(SystemSetting(business_id=business.id, key=key, value=value, description=desc))

    db.commit()
    db.refresh(business)
    return business


@router.get("/{business_id}", response_model=BusinessResponse)
def get_business(
    business_id: int,
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_platform_admin),
):
    b = db.query(Business).filter(Business.id == business_id).first()
    if not b:
        raise HTTPException(status_code=404, detail="Business not found")
    return b


@router.put("/{business_id}", response_model=BusinessResponse)
def update_business(
    business_id: int,
    body: BusinessUpdate,
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_user),
):
    # Platform admins can update any business.
    # Business admins can only update their own business.
    if not current_user.is_platform_admin and current_user.business_id != business_id:
        raise HTTPException(status_code=403, detail="Access denied")

    # Business admins cannot change plan, is_active, is_demo, or Stripe fields
    if not current_user.is_platform_admin:
        protected = {"plan", "is_active", "is_demo", "stripe_customer_id",
                     "stripe_subscription_id", "subscription_tier", "subscription_status"}
        for field in protected:
            body.__dict__.pop(field, None)

    b = db.query(Business).filter(Business.id == business_id).first()
    if not b:
        raise HTTPException(status_code=404, detail="Business not found")

    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(b, field, value)

    db.commit()
    db.refresh(b)
    return b


# ---------------------------------------------------------------------------
# POST /api/businesses/{business_id}/impersonate
# ---------------------------------------------------------------------------

@router.post("/{business_id}/impersonate")
def impersonate_business(
    business_id: int,
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_platform_admin),
):
    """
    Mint a short-lived impersonation token scoped to a tenant's admin user.
    Platform admin only.  Returns a 2-hour access token that behaves exactly
    like the business admin's own token, plus extra claims the frontend uses
    to show the impersonation banner and restore the original session.
    """
    business = db.query(Business).filter(Business.id == business_id).first()
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")

    # Find the first active admin user for this business
    admin_user = (
        db.query(AdminUser)
        .filter(
            AdminUser.business_id == business_id,
            AdminUser.is_active == True,
        )
        .order_by(AdminUser.id)
        .first()
    )
    if not admin_user:
        raise HTTPException(
            status_code=404,
            detail="No active admin user found for this business. "
                   "Create one via the Businesses page first.",
        )

    token_data = {
        "sub":                  admin_user.id,
        "username":             admin_user.username,
        "role":                 admin_user.role,
        "business_id":          business.id,
        "is_platform_admin":    False,
        # Extra claims — used only by the frontend, ignored by all API endpoints
        "impersonating":        True,
        "impersonated_by_id":   current_user.id,
        "impersonated_by_name": current_user.username,
        "business_name":        business.name,
    }

    token = create_access_token(token_data, expires_delta=timedelta(hours=2))

    return {
        "access_token": token,
        "business_name": business.name,
    }
