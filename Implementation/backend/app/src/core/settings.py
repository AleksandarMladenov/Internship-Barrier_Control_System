from typing import Optional
from pydantic import SecretStr, field_validator, ValidationInfo
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # App
    ENV: str = "dev"
    APP_PORT: int = 8000

    # DB parts (used if DATABASE_URL not provided)
    DATABASE_URL: Optional[str] = None
    POSTGRES_USER: str = "parking"
    POSTGRES_PASSWORD: SecretStr = SecretStr("parking")
    POSTGRES_DB: str = "parking"
    POSTGRES_HOST: str = "db"      # use "localhost" if not in Docker
    POSTGRES_PORT: int = 5432

    # Third-party (placeholders)
    STRIPE_SECRET: SecretStr = SecretStr("")
    STRIPE_WEBHOOK_SECRET: SecretStr = SecretStr("")
    PUBLIC_BASE_URL: str = "http://localhost:8000"
    BARRIER_PI_BASE_URL: str = "http://192.168.1.160:5000"
    GOOGLE_APPLICATION_CREDENTIALS: Optional[str] = None
    FIREBASE_STORAGE_BUCKET: Optional[str] = None

    # ---- Auth / JWT / Cookies ----
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    SECRET_KEY: SecretStr = SecretStr("dev-change-me")
    AUTH_COOKIE_NAME: str = "auth"
    AUTH_COOKIE_SECURE: bool = False
    AUTH_COOKIE_SAMESITE: str = "lax"

    INVITE_EXPIRES_MINUTES: int = 60 * 24 * 7  # 7 days
    FRONTEND_BASE_URL: str = "http://localhost:5173"

    # Email (optional)
    EMAIL_ENABLED: bool = False
    SMTP_HOST: str = "smtp.fastmail.com"
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    EMAIL_FROM: str = "no-reply@example.com"

    PRICING_GRACE_MINUTES: int = 0
    PRICING_ROUND_UP: bool = True
    GRACE_AUTOCLOSE_ENABLED: bool = False

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def build_database_url_if_missing(cls, v, info: ValidationInfo):
        # if provided explicitly, keep it
        if isinstance(v, str) and v.strip():
            return v

        # in v2, use info.data to access other field values
        data = info.data or {}
        user = data.get("POSTGRES_USER", "parking")
        pwd = data.get("POSTGRES_PASSWORD", SecretStr("parking"))
        # ensure string password
        if isinstance(pwd, SecretStr):
            pwd = pwd.get_secret_value()
        host = data.get("POSTGRES_HOST", "db")
        port = data.get("POSTGRES_PORT", 5432)
        db = data.get("POSTGRES_DB", "parking")
        return f"postgresql+psycopg://{user}:{pwd}@{host}:{port}/{db}"

settings = Settings()
