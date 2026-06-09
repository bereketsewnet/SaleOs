from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    APP_NAME: str = "SaleOS Telegram"
    APP_ENV: str = "development"
    APP_PORT: int = 8001

    FRONTEND_URL: str = "http://localhost:3001"

    JWT_SECRET: str
    JWT_EXPIRE_MINUTES: int = 60

    DATABASE_URL: str

    REDIS_URL: str = "redis://redis:6379"
    REDIS_DB_TELEGRAM: int = 1

    X_SERVICE_TOKEN: str
    ENCRYPTION_KEY: str

    CORE_SERVICE_URL: str = "http://saleos-core:8000"
    TELEGRAM_WEBHOOK_BASE_URL: str = "http://localhost/api/v1/telegram/webhook"

    GEMINI_API_KEY: str = ""
    OPENAI_API_KEY: str = ""

    MINIO_ENDPOINT: str = "minio:9000"
    MINIO_ACCESS_KEY: str
    MINIO_SECRET_KEY: str
    MINIO_BUCKET_MEDIA: str = "merchant-media"
    MINIO_USE_SSL: bool = False


settings = Settings()
