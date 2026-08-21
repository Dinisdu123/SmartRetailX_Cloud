import os
from dotenv import load_dotenv

load_dotenv()


class Settings:

    # ============================================================
    # JWT Configuration
    # ============================================================

    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")

    JWT_ALGORITHM = "HS256"

    JWT_ISSUER = "user-management-service"

    JWT_AUDIENCE = "smartretailx"

    # ============================================================
    # PostgreSQL Configuration
    # ============================================================

    DATABASE_URL = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:password@localhost:5432/orderdb"
    )

    # ============================================================
    # AWS / SQS Configuration
    # ============================================================

    AWS_REGION = os.getenv(
        "AWS_REGION",
        "us-east-1"
    )

    # Only set this for LOCAL DEV (e.g. ElasticMQ on localhost:9324).
    # In AWS this must stay empty so boto3 hits real SQS endpoints.
    SQS_ENDPOINT = os.getenv(
        "SQS_ENDPOINT",
        ""
    )

    AWS_ACCESS_KEY_ID = os.getenv(
        "AWS_ACCESS_KEY_ID",
        "local"
    )

    AWS_SECRET_ACCESS_KEY = os.getenv(
        "AWS_SECRET_ACCESS_KEY",
        "local"
    )

    SQS_QUEUE_URL = os.getenv(
        "SQS_QUEUE_URL",
        "http://localhost:9324/000000000000/orders-queue"
    )

    # ============================================================
    # Product Catalogue Service
    # ============================================================

    PRODUCT_SERVICE_URL = os.getenv(
        "PRODUCT_SERVICE_URL",
        "http://localhost:8002"
    )

    # ============================================================
    # Circuit Breaker Configuration
    # ============================================================

    CIRCUIT_BREAKER_FAILURE_THRESHOLD = int(
        os.getenv(
            "CIRCUIT_BREAKER_FAILURE_THRESHOLD",
            "3"
        )
    )

    CIRCUIT_BREAKER_RECOVERY_TIMEOUT = int(
        os.getenv(
            "CIRCUIT_BREAKER_RECOVERY_TIMEOUT",
            "30"
        )
    )

    # ============================================================
    # Application Configuration
    # ============================================================

    APP_NAME = (
        "SmartRetailX Order Processing Service"
    )

    APP_VERSION = "1.0.0"

    APP_ENVIRONMENT = os.getenv(
        "APP_ENVIRONMENT",
        "development"
    )

    APP_DESCRIPTION = (
        "Handles order creation, status management "
        "and event publishing"
    )

    def validate(self):

        if not self.JWT_SECRET_KEY:

            raise ValueError(
                "JWT_SECRET_KEY environment variable is not set"
            )

        return True


settings = Settings()

settings.validate()