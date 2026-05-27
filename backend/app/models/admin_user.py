"""Admin user model — supports both platform-level and business-level admins."""

from datetime import datetime
from sqlalchemy import String, Boolean, Integer, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class AdminUser(Base):
    __tablename__ = "admin_users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # NULL business_id = Space Coast Studios platform admin (can see all tenants)
    # Non-null business_id = admin scoped to that specific business only
    business_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("businesses.id"), nullable=True, index=True
    )

    username: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # Separate from username — used for password reset emails.
    # For self-signup users, username == email.
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(20), default="admin")
    # Platform roles:  "platform_admin"
    # Business roles:  "admin", "dispatcher", "viewer"
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Password reset (used for both new-user setup and forgot-password)
    password_reset_token: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    password_reset_expires: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Relationships
    business = relationship("Business", back_populates="admin_users")

    @property
    def is_platform_admin(self) -> bool:
        return self.business_id is None
