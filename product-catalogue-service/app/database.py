import boto3

from app.config.settings import settings


def get_dynamodb():
    """
    Create and return a DynamoDB resource.
    """

    kwargs = {
        "region_name": settings.AWS_REGION
    }

    # Local DynamoDB configuration
    if settings.DYNAMODB_ENDPOINT:
        kwargs["endpoint_url"] = settings.DYNAMODB_ENDPOINT
        kwargs["aws_access_key_id"] = settings.AWS_ACCESS_KEY_ID
        kwargs["aws_secret_access_key"] = settings.AWS_SECRET_ACCESS_KEY

    return boto3.resource(
        "dynamodb",
        **kwargs
    )


def get_table():
    """
    Return the configured products DynamoDB table.
    """

    dynamodb = get_dynamodb()

    return dynamodb.Table(
        settings.DYNAMODB_TABLE
    )


import logging

logger = logging.getLogger("product-catalogue-service")

def check_dynamodb_connection() -> bool:
    try:
        dynamodb = get_dynamodb()
        dynamodb.meta.client.list_tables()
        return True
    except Exception as e:
        logger.error(f"DynamoDB connection failed: {type(e).__name__}: {str(e)}")
        return False