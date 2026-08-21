import boto3

from app.config.settings import settings


def get_dynamodb():

    kwargs = {
        "region_name": settings.AWS_REGION
    }

    # Only use endpoint_url for LOCAL development
    if settings.DYNAMODB_ENDPOINT:
        kwargs["endpoint_url"] = settings.DYNAMODB_ENDPOINT
        kwargs["aws_access_key_id"] = settings.AWS_ACCESS_KEY_ID
        kwargs["aws_secret_access_key"] = settings.AWS_SECRET_ACCESS_KEY

    return boto3.resource(
        "dynamodb",
        **kwargs
    )


def get_inventory_table():

    dynamodb = get_dynamodb()

    return dynamodb.Table(
        settings.DYNAMODB_INVENTORY_TABLE
    )


def check_dynamodb_connection() -> bool:

    try:

        dynamodb = get_dynamodb()

        dynamodb.meta.client.describe_table(
            TableName=settings.DYNAMODB_INVENTORY_TABLE
        )

        return True

    except Exception:

        return False