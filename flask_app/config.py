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
    # local = FAQ only; llm = Together AI (Adaption fine-tune) with FAQ fallback
    VAULTI_BACKEND = os.environ.get("VAULTI_BACKEND", "local")
    MPESA_WEBHOOK_SECRET = os.environ.get("MPESA_WEBHOOK_SECRET", "demo-secret")
    SCHEDULER_ENABLED = os.environ.get("SCHEDULER_ENABLED", "1") == "1"

    # Adaption trains; Together serves the LoRA / fine-tune
    ADAPTION_API_KEY = os.environ.get("ADAPTION_API_KEY", "")
    TOGETHER_API_KEY = os.environ.get("TOGETHER_API_KEY", "")
    VAULTI_MODEL_ID = os.environ.get("VAULTI_MODEL_ID", "")

    # Cognaria Kenyan TTS
    COGNARIA_API_KEY = os.environ.get("COGNARIA_API_KEY", "")
    COGNARIA_API_BASE = os.environ.get("COGNARIA_API_BASE", "https://api.cognariai.com")
    COGNARIA_VOICE_EN = os.environ.get("COGNARIA_VOICE_EN", "kenya_female_1")
    COGNARIA_VOICE_SW = os.environ.get("COGNARIA_VOICE_SW", "zuri_ke")

    # Resend email
    RESEND_API_KEY = os.environ.get("RESEND_API_KEY", "")
    EMAIL_FROM = os.environ.get("EMAIL_FROM", "ChamaVault <onboarding@resend.dev>")

    LARGE_PAYOUT_SHARE = 0.30   # payout >= 30% of pool counts as "large"
    LARGE_PAYOUT_WINDOW_DAYS = 2  # ...if made within 2 days after contribution day


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    WTF_CSRF_ENABLED = False
    SCHEDULER_ENABLED = False
    VAULTI_BACKEND = "local"
