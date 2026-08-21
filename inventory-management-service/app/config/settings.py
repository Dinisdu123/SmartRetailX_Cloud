import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    # ============================================================
    # JWT CONFIGURATION
    # ============================================================

    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
    JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
    JWT_ISSUER = os.getenv("JWT_ISSUER", "user-management-service")
    JWT_AUDIENCE = os.getenv("JWT_AUDIENCE", "smartretailx")

    # ============================================================
    # DYNAMODB CONFIGURATION
    # ============================================================

    AWS_REGION = os.getenv(
    "AWS_REGION",
    "ap-south-1"
)

    DYNAMODB_ENDPOINT = os.getenv(
    "DYNAMODB_ENDPOINT",
    ""
)

    AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")

    DYNAMODB_INVENTORY_TABLE = os.getenv(
        "DYNAMODB_INVENTORY_TABLE",
        "inventory"
    )

    # ============================================================
    # SQS / SNS CONFIGURATION
    # ============================================================

    SQS_ENDPOINT = os.getenv(
        "SQS_ENDPOINT",
        "http://localhost:9324"
    )

    SNS_ENDPOINT = os.getenv(
        "SNS_ENDPOINT",
        "http://localhost:9324"
    )

    SQS_QUEUE_URL = os.getenv(
        "SQS_QUEUE_URL",
        "http://localhost:9324/000000000000/orders-queue"
    )

    NOTIFICATION_QUEUE_URL = os.getenv(
        "NOTIFICATION_QUEUE_URL",
        "http://localhost:9324/000000000000/notification-queue"
    )

    # ============================================================
    # APPLICATION CONFIGURATION
    # ============================================================

    APP_NAME = "SmartRetailX Inventory Management Service"
    APP_VERSION = "1.0.0"

    APP_ENVIRONMENT = os.getenv(
        "APP_ENVIRONMENT",
        "development"
    )

    APP_DESCRIPTION = (
        "Manages product stock levels and processes inventory events"
    )

    # ============================================================
    # VALIDATION
    # ============================================================

    def validate(self):
        if not self.JWT_SECRET_KEY:
            raise ValueError(
                "JWT_SECRET_KEY environment variable is not set"
            )

        return True


settings = Settings()
settings.validate()