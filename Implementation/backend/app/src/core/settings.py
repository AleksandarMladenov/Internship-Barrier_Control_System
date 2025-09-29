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
    GOOGLE_APPLICATION_CREDENTIALS: Optional[str] = None
    FIREBASE_STORAGE_BUCKET: Optional[str] = None

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
