import os
from dotenv import load_dotenv

load_dotenv()


class Settings:

    # ============================================
    # JWT Configuration
    # ============================================

    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")

    JWT_ALGORITHM = "HS256"

    JWT_ISSUER = "user-management-service"
    JWT_AUDIENCE = "smartretailx"

    # ============================================
    # DynamoDB Configuration
    # ============================================

    AWS_REGION = os.getenv("AWS_REGION", "us-east-1")

    # Local DynamoDB endpoint
    # Set to empty when using real AWS DynamoDB
    DYNAMODB_ENDPOINT = os.getenv("DYNAMODB_ENDPOINT") or None

    AWS_ACCESS_KEY_ID = os.getenv(
        "AWS_ACCESS_KEY_ID",
        "local"
    )

    AWS_SECRET_ACCESS_KEY = os.getenv(
        "AWS_SECRET_ACCESS_KEY",
        "local"
    )

    DYNAMODB_TABLE = os.getenv(
    "DYNAMODB_TABLE",
    os.getenv("DYNAMODB_PRODUCTS_TABLE", "products")  # support both names
)

    # ============================================
    # Application Configuration
    # ============================================

    APP_NAME = "SmartRetailX Product Catalogue Service"

    APP_VERSION = "1.0.0"

    APP_DESCRIPTION = (
        "Handles product listings, search, filtering "
        "and catalogue management"
    )

    def validate(self):
        """
        Validate required configuration.
        """

        if not self.JWT_SECRET_KEY:
            raise ValueError(
                "JWT_SECRET_KEY environment variable is not set"
            )

        return True


settings = Settings()
settings.validate()