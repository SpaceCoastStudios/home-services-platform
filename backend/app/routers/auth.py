"""Authentication endpoints."""

import logging
import secrets
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.admin_user import AdminUser
from app.schemas.auth import LoginRequest, TokenResponse, RefreshRequest
from app.utils.auth import verify_password, create_access_token, create_refresh_token, decode_token, build_token_data, hash_password

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["auth"])

DASHBOARD_URL = "https://dashboard.spacecoaststudios.com"


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(AdminUser).filter(AdminUser.username == body.username).first()
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account disabled")

    token_data = build_token_data(user)
    return TokenResponse(
        access_token=create_access_token(token_data),
        refresh_token=create_refresh_token(token_data),
    )


@router.post("/refresh", response_model=TokenResponse)
def refresh(body: RefreshRequest, db: Session = Depends(get_db)):
    payload = decode_token(body.refresh_token)
    if payload.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")

    user = db.query(AdminUser).filter(AdminUser.id == payload.get("sub")).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    token_data = build_token_data(user)
    return TokenResponse(
        access_token=create_access_token(token_data),
        refresh_token=create_refresh_token(token_data),
    )


@router.post("/set-password")
def set_password(body: dict, db: Session = Depends(get_db)):
    """
    Set a new password using a password-reset / account-setup token.
    Token is generated during Stripe checkout provisioning or manual admin creation.

    Body: { "token": "...", "password": "...", "confirm_password": "..." }
    """
    token    = (body.get("token") or "").strip()
    password = body.get("password") or ""
    confirm  = body.get("confirm_password") or ""

    if not token:
        raise HTTPException(status_code=400, detail="Token is required")
    if len(password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")
    if password != confirm:
        raise HTTPException(status_code=400, detail="Passwords do not match")

    user = db.query(AdminUser).filter(AdminUser.password_reset_token == token).first()
    if not user:
        raise HTTPException(status_code=400, detail="Invalid or expired link")

    expires = user.password_reset_expires
    if expires:
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=timezone.utc)
        if datetime.now(timezone.utc) > expires:
            raise HTTPException(status_code=400, detail="This link has expired. Please contact support.")

    user.password_hash = hash_password(password)
    user.password_reset_token = None
    user.password_reset_expires = None
    db.commit()

    return {"message": "Password set successfully. You can now log in."}


@router.post("/forgot-password")
def forgot_password(body: dict, db: Session = Depends(get_db)):
    """
    Request a password reset email.
    Always returns 200 regardless of whether the email exists (prevents enumeration).

    Body: { "email": "user@example.com" }
    """
    email = (body.get("email") or "").strip().lower()
    if not email:
        raise HTTPException(status_code=400, detail="Email is required")

    # Find the user — silently succeed even if not found
    user = db.query(AdminUser).filter(AdminUser.email == email).first()

    if user and user.is_active:
        reset_token = secrets.token_urlsafe(48)
        expires = datetime.now(timezone.utc) + timedelta(hours=1)

        user.password_reset_token = reset_token
        user.password_reset_expires = expires
        db.commit()

        _send_password_reset_email(email, reset_token)
        logger.info("Password reset token issued for %s", email)
    else:
        logger.info("Forgot-password request for unknown/inactive email: %s", email)

    # Always return success to avoid leaking which emails are registered
    return {"message": "If that email is registered, a password reset link has been sent."}


def _send_password_reset_email(email: str, token: str):
    """Send a password reset email via SendGrid."""
    from app.services.notifications import send_email
    reset_url = f"{DASHBOARD_URL}/set-password?token={token}&mode=reset"
    subject = "Space Coast Studios — Password Reset Request"
    plain = (
        f"Hi,\n\n"
        f"We received a request to reset the password for your Space Coast Studios account.\n\n"
        f"Click the link below to choose a new password:\n"
        f"{reset_url}\n\n"
        f"This link expires in 1 hour.\n\n"
        f"If you didn't request a password reset, you can ignore this email — your password won't change.\n\n"
        f"— Space Coast Studios"
    )
    html = f"""
    <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;padding:32px;">
      <h2 style="color:#1e40af;">Password Reset Request</h2>
      <p>We received a request to reset the password for your Space Coast Studios account.</p>
      <p>Click the button below to choose a new password:</p>
      <p style="text-align:center;margin:32px 0;">
        <a href="{reset_url}"
           style="background:#2563eb;color:#fff;padding:14px 28px;border-radius:8px;
                  text-decoration:none;font-weight:bold;font-size:16px;">
          Reset My Password
        </a>
      </p>
      <p style="color:#6b7280;font-size:13px;">
        This link expires in <strong>1 hour</strong>.<br>
        If you didn't request a password reset, you can safely ignore this email.
      </p>
      <hr style="border:none;border-top:1px solid #e5e7eb;margin:24px 0;">
      <p style="color:#9ca3af;font-size:12px;">Space Coast Studios &mdash; support@spacecoaststudios.com</p>
    </div>
    """
    try:
        send_email(email, subject, html, plain)
        logger.info("Password reset email sent to %s", email)
    except Exception as exc:
        logger.error("Failed to send password reset email to %s: %s", email, exc)
