from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # App
    APP_NAME: str = "SaleOS"
    APP_ENV: str = "development"
    FRONTEND_URL: str = "http://localhost:3000"
    BACKEND_URL: str = "http://localhost:8000"

    # JWT
    JWT_SECRET: str
    JWT_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # Database
    DATABASE_URL: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str

    # Redis
    REDIS_URL: str
    REDIS_DB_CORE: int = 0
    REDIS_DB_TELEGRAM: int = 1
    REDIS_DB_TIKTOK: int = 2
    REDIS_DB_INSTAGRAM: int = 3
    REDIS_DB_FACEBOOK: int = 4

    # Security
    X_SERVICE_TOKEN: str
    ENCRYPTION_KEY: str

    # AI
    GEMINI_API_KEY: str = ""
    OPENAI_API_KEY: str = ""

    # MinIO
    MINIO_ENDPOINT: str = "minio:9000"
    # Browser-facing endpoint — used to sign presigned URLs so the signature
    # matches the host the browser actually connects to.
    MINIO_PUBLIC_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str
    MINIO_SECRET_KEY: str
    MINIO_BUCKET_OCR: str = "ocr-receipts"
    MINIO_BUCKET_MEDIA: str = "merchant-media"
    MINIO_BUCKET_RECEIPTS: str = "payment-receipts"
    MINIO_USE_SSL: bool = False

    # Microservice URLs
    TELEGRAM_SERVICE_URL: str = "http://saleos-telegram:8001"
    TIKTOK_SERVICE_URL: str = "http://saleos-tiktok:8002"
    INSTAGRAM_SERVICE_URL: str = "http://saleos-instagram:8003"
    FACEBOOK_SERVICE_URL: str = "http://saleos-facebook:8004"

    # Telegram
    TELEGRAM_WEBHOOK_BASE_URL: str = "http://localhost/api/v1/telegram/webhook"

    # OCR
    EXTERNAL_ETHIOPIAN_BANK_OCR_API_URL: str = "https://ocr.placeholder.com/api/v1/verify-receipt"
    EXTERNAL_ETHIOPIAN_BANK_OCR_API_TOKEN: str = "placeholder"

    # Email
    SMTP_HOST: str = "smtp.mailgun.org"
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""

    # WebSocket
    WS_SECRET: str


settings = Settings()
