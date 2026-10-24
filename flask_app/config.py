"""App configuration: secrets, database, and demo switches (env vars override defaults)."""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-only-change-me")
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", f"sqlite:///{BASE_DIR / 'instance' / 'chamavault.db'}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"

    TIMEZONE = "Africa/Nairobi"
    SMS_BACKEND = "mock"        # swap for "africastalking" once a real service class exists
    MPESA_BACKEND = "mock"      # swap for "daraja" later
    VAULTI_BACKEND = "local"    # swap for "llm" once an API key is wired in
    MPESA_WEBHOOK_SECRET = os.environ.get("MPESA_WEBHOOK_SECRET", "demo-secret")
    SCHEDULER_ENABLED = os.environ.get("SCHEDULER_ENABLED", "1") == "1"

    LARGE_PAYOUT_SHARE = 0.30   # payout >= 30% of pool counts as "large"
    LARGE_PAYOUT_WINDOW_DAYS = 2  # ...if made within 2 days after contribution day


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    WTF_CSRF_ENABLED = False
    SCHEDULER_ENABLED = False
