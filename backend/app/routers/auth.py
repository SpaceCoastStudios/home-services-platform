"""Authentication endpoints."""

from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.admin_user import AdminUser
from app.schemas.auth import LoginRequest, TokenResponse, RefreshRequest
from app.utils.auth import verify_password, create_access_token, create_refresh_token, decode_token, build_token_data, hash_password

router = APIRouter(prefix="/api/auth", tags=["auth"])


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
