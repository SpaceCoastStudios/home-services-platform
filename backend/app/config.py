"""Application configuration and settings."""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "Home Services Platform"
    APP_VERSION: str = "1.0.0-mvp"
    DEBUG: bool = True
    SECRET_KEY: str = "change-me-in-production"
    API_PREFIX: str = "/api"

    # Database
    # Locally: sqlite:///./homeservices.db
    # Production: set DATABASE_URL to the DigitalOcean PostgreSQL connection string.
    # DigitalOcean provides "postgres://..." — we fix that to "postgresql+psycopg2://..." below.
    DATABASE_URL: str = "sqlite:///./homeservices.db"

    # JWT Auth
    JWT_SECRET_KEY: str = "change-me-jwt-secret"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Twilio
    TWILIO_ACCOUNT_SID: Optional[str] = None
    TWILIO_AUTH_TOKEN: Optional[str] = None
    TWILIO_PHONE_NUMBER: Optional[str] = None

    # LLM (AI Agent)
    LLM_PROVIDER: str = "anthropic"  # "anthropic" or "openai"
    ANTHROPIC_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    LLM_MODEL: str = "claude-sonnet-4-20250514"

    # Stripe
    STRIPE_SECRET_KEY: Optional[str] = None
    STRIPE_PUBLISHABLE_KEY: str = "pk_live_51TM7kZ2MJMR8rAcZ2jSBcduwtelYsLikfR9OsPACEOypphYntZ1MmdpSK7lFdMb8egcatVty5vL5h4SiB2X7sc2n00HqCzzbqd"
    STRIPE_WEBHOOK_SECRET: Optional[str] = None

    # Stripe Product IDs
    STRIPE_PRODUCT_STARTER: str = "prod_Uail0oXz9jO2Nw"
    STRIPE_PRODUCT_PROFESSIONAL: str = "prod_Uailjx0LeRYgYw"

    # Stripe Price IDs — Standard
    STRIPE_PRICE_STARTER_SETUP: str = "price_1TbXKM2MJMR8rAcZfEKeo13B"
    STRIPE_PRICE_STARTER_MONTHLY: str = "price_1TbXKN2MJMR8rAcZ8ageyctL"
    STRIPE_PRICE_PRO_SETUP: str = "price_1TbXKN2MJMR8rAcZIiW0KPMT"
    STRIPE_PRICE_PRO_MONTHLY: str = "price_1TbXKO2MJMR8rAcZh0yQdVOv"

    # Stripe Price IDs — Founding Client
    STRIPE_PRICE_STARTER_SETUP_FOUNDING: str = "price_1TbXKN2MJMR8rAcZvreEPLwo"
    STRIPE_PRICE_STARTER_MONTHLY_FOUNDING: str = "price_1TbXKN2MJMR8rAcZF8PV52FQ"
    STRIPE_PRICE_PRO_SETUP_FOUNDING: str = "price_1TbXKO2MJMR8rAcZ9MRzpF2s"
    STRIPE_PRICE_PRO_MONTHLY_FOUNDING: str = "price_1TbXKO2MJMR8rAcZMiHThRka"

    # Email (SendGrid)
    SENDGRID_API_KEY: Optional[str] = None
    # Accept either FROM_EMAIL or SENDGRID_FROM_EMAIL in .env (both map to the same thing)
    FROM_EMAIL: str = "noreply@homeservices.com"
    SENDGRID_FROM_EMAIL: Optional[str] = None   # alias — if set, overrides FROM_EMAIL
    FROM_NAME: str = "Home Services"
    SENDGRID_FROM_NAME: Optional[str] = None    # alias — if set, overrides FROM_NAME

    # Scheduling Defaults (overridable via system_settings table)
    DEFAULT_SLOT_GRANULARITY_MINUTES: int = 30
    DEFAULT_BUFFER_MINUTES: int = 15
    DEFAULT_MAX_ADVANCE_BOOKING_DAYS: int = 30
    DEFAULT_MIN_LEAD_TIME_HOURS: int = 2
    DEFAULT_MAX_APPOINTMENTS_PER_TECH_PER_DAY: int = 8
    DEFAULT_ALLOW_SAME_DAY_BOOKING: bool = True

    # Contact Form
    CONTACT_AUTO_RESPOND: bool = True  # False = hold for human review
    CONTACT_MAX_SUGGESTED_SLOTS: int = 5
    CONTACT_INCLUDE_PRICING: bool = True

    # Base URL for calendar links and public-facing URLs
    BASE_URL: str = "http://localhost:8000"

    # CORS — comma-separated list of allowed frontend origins
    # In production set to: https://dashboard.spacecoaststudios.com,https://spacecoaststudios.com
    ALLOWED_ORIGINS: str = "http://localhost:5173,http://localhost:3000"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    @property
    def database_url_fixed(self) -> str:
        """Return a SQLAlchemy-compatible database URL.
        DigitalOcean may give 'postgres://' or 'postgresql://' —
        SQLAlchemy 2.x needs 'postgresql+psycopg2://' for psycopg2 driver."""
        url = self.DATABASE_URL
        if url.startswith("postgres://"):
            url = "postgresql+psycopg2://" + url[len("postgres://"):]
        elif url.startswith("postgresql://"):
            url = "postgresql+psycopg2://" + url[len("postgresql://"):]
        return url

    @property
    def sender_email(self) -> str:
        """Resolved platform sender address — prefers SENDGRID_FROM_EMAIL over FROM_EMAIL."""
        return self.SENDGRID_FROM_EMAIL or self.FROM_EMAIL

    @property
    def sender_name(self) -> str:
        """Resolved platform sender name — prefers SENDGRID_FROM_NAME over FROM_NAME."""
        return self.SENDGRID_FROM_NAME or self.FROM_NAME


settings = Settings()
