"""Contact form submission and management endpoints — scoped by business_id."""

from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.admin_user import AdminUser
from app.models.contact_submission import ContactSubmission
from app.models.customer import Customer
from app.schemas.contact import (
    ContactFormSubmit,
    ContactSubmissionResponse,
    ContactSubmissionUpdate,
    ManualResponseRequest,
)
from app.utils.auth import get_current_user, get_business_id_for_user

router = APIRouter(tags=["contact"])


@router.post("/contact/submit", response_model=ContactSubmissionResponse, status_code=201)
def submit_contact_form(
    body: ContactFormSubmit,
    background_tasks: BackgroundTasks,
    business_id: int = Query(..., description="Business ID — identifies which tenant this form belongs to"),
    db: Session = Depends(get_db),
):
    """
    Public endpoint — receives contact form submissions from a tenant website.
    Saves the submission and fires the AI auto-responder as a background task.
    """
    # Try to match to existing customer by phone or email, scoped to this business
    customer = None
    if body.phone:
        customer = (
            db.query(Customer)
            .filter(Customer.phone == body.phone, Customer.business_id == business_id)
            .first()
        )
    if not customer and body.email:
        customer = (
            db.query(Customer)
            .filter(Customer.email == body.email, Customer.business_id == business_id)
            .first()
        )

    submission = ContactSubmission(
        business_id=business_id,
        customer_id=customer.id if customer else None,
        name=body.name,
        email=body.email,
        phone=body.phone,
        service_requested=body.service_requested,
        message=body.message,
        preferred_date=body.preferred_date,
        preferred_time=body.preferred_time,
        status="new",
    )
    db.add(submission)
    db.commit()
    db.refresh(submission)

    # Fire AI auto-responder in background (non-blocking)
    if settings.CONTACT_AUTO_RESPOND and settings.ANTHROPIC_API_KEY:
        from app.services.contact_responder import run_contact_responder
        background_tasks.add_task(run_contact_responder, db, submission.id)

    return submission


# --- Admin endpoints ---

@router.get("/api/contact-submissions", response_model=list[ContactSubmissionResponse])
def list_submissions(
    status: Optional[str] = None,
    business_id: Optional[int] = Query(None),
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_user),
):
    bid = get_business_id_for_user(current_user, business_id)
    query = db.query(ContactSubmission).filter(ContactSubmission.business_id == bid)
    if status:
        query = query.filter(ContactSubmission.status == status)
    return query.order_by(ContactSubmission.created_at.desc()).offset(skip).limit(limit).all()


@router.get("/api/contact-submissions/{submission_id}", response_model=ContactSubmissionResponse)
def get_submission(
    submission_id: int,
    business_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_user),
):
    bid = get_business_id_for_user(current_user, business_id)
    sub = (
        db.query(ContactSubmission)
        .filter(ContactSubmission.id == submission_id, ContactSubmission.business_id == bid)
        .first()
    )
    if not sub:
        raise HTTPException(status_code=404, detail="Submission not found")
    return sub


@router.put("/api/contact-submissions/{submission_id}", response_model=ContactSubmissionResponse)
def update_submission(
    submission_id: int,
    body: ContactSubmissionUpdate,
    business_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_user),
):
    bid = get_business_id_for_user(current_user, business_id)
    sub = (
        db.query(ContactSubmission)
        .filter(ContactSubmission.id == submission_id, ContactSubmission.business_id == bid)
        .first()
    )
    if not sub:
        raise HTTPException(status_code=404, detail="Submission not found")

    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(sub, field, value)

    db.commit()
    db.refresh(sub)
    return sub


@router.post("/api/contact-submissions/{submission_id}/respond", response_model=ContactSubmissionResponse)
def trigger_ai_response(
    submission_id: int,
    background_tasks: BackgroundTasks,
    business_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_user),
):
    """
    Admin endpoint: manually (re-)trigger the AI auto-responder for a submission.
    Useful for testing or re-sending a response.
    """
    bid = get_business_id_for_user(current_user, business_id)
    sub = (
        db.query(ContactSubmission)
        .filter(ContactSubmission.id == submission_id, ContactSubmission.business_id == bid)
        .first()
    )
    if not sub:
        raise HTTPException(status_code=404, detail="Submission not found")

    if not settings.ANTHROPIC_API_KEY:
        raise HTTPException(status_code=503, detail="AI responder not configured (missing ANTHROPIC_API_KEY)")

    from app.services.contact_responder import run_contact_responder
    background_tasks.add_task(run_contact_responder, db, sub.id)

    return sub


@router.post("/api/contact-submissions/{submission_id}/approve", response_model=ContactSubmissionResponse)
def approve_ai_response(
    submission_id: int,
    business_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_user),
):
    """
    Approve and send a pending AI-drafted response.
    Only valid when submission status is 'pending_approval'.
    """
    from datetime import datetime, timezone
    from app.models.business import Business
    from app.services.contact_responder import _send_reply_email, _send_reply_sms

    bid = get_business_id_for_user(current_user, business_id)
    sub = (
        db.query(ContactSubmission)
        .filter(ContactSubmission.id == submission_id, ContactSubmission.business_id == bid)
        .first()
    )
    if not sub:
        raise HTTPException(status_code=404, detail="Submission not found")
    if sub.status != "pending_approval":
        raise HTTPException(status_code=400, detail="Submission is not pending approval")
    if not sub.ai_response:
        raise HTTPException(status_code=400, detail="No AI response to approve")

    business = db.query(Business).filter(Business.id == bid).first()
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")

    _send_reply_email(business, sub, sub.ai_response)
    if sub.phone:
        _send_reply_sms(business, sub, sub.ai_response)

    sub.status = "ai_responded"
    sub.responded_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(sub)
    return sub


@router.post("/api/contact-submissions/{submission_id}/manual-response", response_model=ContactSubmissionResponse)
def send_manual_response(
    submission_id: int,
    body: ManualResponseRequest,
    business_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_user),
):
    """
    Admin endpoint: send a manually-written reply to a customer.
    Bypasses AI — staff writes the message directly.
    """
    from datetime import datetime, timezone
    from app.models.business import Business
    from app.services.contact_responder import _send_reply_email, _send_reply_sms

    bid = get_business_id_for_user(current_user, business_id)
    sub = (
        db.query(ContactSubmission)
        .filter(ContactSubmission.id == submission_id, ContactSubmission.business_id == bid)
        .first()
    )
    if not sub:
        raise HTTPException(status_code=404, detail="Submission not found")

    business = db.query(Business).filter(Business.id == bid).first()
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")

    if body.send_email:
        _send_reply_email(business, sub, body.message)

    if body.send_sms and sub.phone:
        _send_reply_sms(business, sub, body.message)

    sub.ai_response = body.message
    sub.status = "responded"
    sub.responded_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(sub)
    return sub
