import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    # ============================================================
    # JWT CONFIGURATION
    # ============================================================

    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
    JWT_REFRESH_SECRET_KEY = os.getenv("JWT_REFRESH_SECRET_KEY")

    JWT_ALGORITHM = "HS256"

    JWT_ACCESS_TOKEN_EXPIRE_HOURS = int(
        os.getenv("ACCESS_TOKEN_EXPIRE_HOURS", "1")
    )

    JWT_REFRESH_TOKEN_EXPIRE_DAYS = int(
        os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7")
    )

    JWT_ISSUER = "user-management-service"
    JWT_AUDIENCE = "smartretailx"

    # ============================================================
    # DATABASE CONFIGURATION
    # ============================================================

    # If DATABASE_URL is provided directly (local dev / docker-compose), use it.
    # Otherwise build it from the separate DB_HOST/DB_USERNAME/DB_PASSWORD
    # secrets that ECS injects from Secrets Manager.
    _db_url = os.getenv("DATABASE_URL")
    if not _db_url:
        _db_host = os.getenv("DB_HOST")
        _db_user = os.getenv("DB_USERNAME")
        _db_pass = os.getenv("DB_PASSWORD")
        _db_name = os.getenv("DB_NAME", "userdb")
        if _db_host and _db_user and _db_pass:
            _db_url = f"postgresql://{_db_user}:{_db_pass}@{_db_host}:5432/{_db_name}"
        else:
            _db_url = "postgresql://postgres:password@localhost:5432/userdb"

    DATABASE_URL = _db_url

    # ============================================================
    # APPLICATION CONFIGURATION
    # ============================================================

    APP_NAME = "SmartRetailX User Management Service"
    APP_VERSION = "1.0.0"

    APP_DESCRIPTION = (
        "Handles user registration, authentication, "
        "authorization and profile management"
    )

    # ============================================================
    # CORS CONFIGURATION
    # ============================================================

    CORS_ORIGINS = [
        origin.strip()
        for origin in os.getenv(
            "CORS_ORIGINS",
            "http://localhost:5173,http://localhost:5174"
        ).split(",")
        if origin.strip()
    ]

    # ============================================================
    # SECURITY CONFIGURATION
    # ============================================================

    MAX_FAILED_LOGIN_ATTEMPTS = int(
        os.getenv("MAX_FAILED_LOGIN_ATTEMPTS", "5")
    )

    ACCOUNT_LOCK_MINUTES = int(
        os.getenv("ACCOUNT_LOCK_MINUTES", "15")
    )

    # ============================================================
    # VALIDATION
    # ============================================================

    def validate(self):
        """Validate required configuration."""

        if not self.JWT_SECRET_KEY:
            raise ValueError(
                "JWT_SECRET_KEY environment variable is not set"
            )

        if not self.JWT_REFRESH_SECRET_KEY:
            raise ValueError(
                "JWT_REFRESH_SECRET_KEY environment variable is not set"
            )

        if len(self.JWT_SECRET_KEY) < 32:
            raise ValueError(
                "JWT_SECRET_KEY must contain at least 32 characters"
            )

        if len(self.JWT_REFRESH_SECRET_KEY) < 32:
            raise ValueError(
                "JWT_REFRESH_SECRET_KEY must contain at least 32 characters"
            )

        if self.JWT_SECRET_KEY == self.JWT_REFRESH_SECRET_KEY:
            raise ValueError(
                "JWT access and refresh secrets must be different"
            )

        return True


settings = Settings()
settings.validate()