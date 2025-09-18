from typing import Optional
from pydantic import SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # Pydantic v2 config
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # App
    ENV: str = "dev"
    APP_PORT: int = 8000

    # Database (either provide DATABASE_URL directly or parts below)
    DATABASE_URL: Optional[str] = None
    POSTGRES_USER: str = "parking"
    POSTGRES_PASSWORD: SecretStr = SecretStr("parking")
    POSTGRES_DB: str = "parking"
    POSTGRES_HOST: str = "db"
    POSTGRES_PORT: int = 5432

    # Third-party (leave empty until needed)
    STRIPE_SECRET: SecretStr = SecretStr("")
    STRIPE_WEBHOOK_SECRET: SecretStr = SecretStr("")
    GOOGLE_APPLICATION_CREDENTIALS: Optional[str] = None  # e.g., /run/secrets/firebase_sa
    FIREBASE_STORAGE_BUCKET: Optional[str] = None

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def build_database_url_if_missing(cls, v, values):
        if v and isinstance(v, str) and v.strip():
            return v
        # Build a sane default for dev/docker
        user = values.get("POSTGRES_USER", "parking")
        pwd = values.get("POSTGRES_PASSWORD", SecretStr("parking")).get_secret_value()
        db = values.get("POSTGRES_DB", "parking")
        host = values.get("POSTGRES_HOST", "db")
        port = values.get("POSTGRES_PORT", 5432)
        return f"postgresql+psycopg://{user}:{pwd}@{host}:{port}/{db}"

settings = Settings()
