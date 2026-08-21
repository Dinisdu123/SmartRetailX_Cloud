import boto3
import json
import os

dynamodb = boto3.resource("dynamodb", region_name=os.environ.get("AWS_REGION", "ap-south-1"))
sqs = boto3.client("sqs", region_name=os.environ.get("AWS_REGION", "ap-south-1"))

INVENTORY_TABLE = os.environ["INVENTORY_TABLE"]
NOTIFICATIONS_QUEUE_URL = os.environ["NOTIFICATIONS_QUEUE_URL"]


def lambda_handler(event, context):
    """
    Scheduled Lambda (triggered by EventBridge) that scans the
    inventory table for items at or below their reorder threshold,
    and publishes a LowStockAlert event to SQS for each one found.
    """

    table = dynamodb.Table(INVENTORY_TABLE)

    response = table.scan()
    items = response.get("Items", [])

    alerts_sent = 0

    for item in items:
        stock = int(item.get("stock_quantity", 0))
        threshold = int(item.get("reorder_threshold", 10))

        if stock <= threshold:
            message = {
                "event_type": "LowStockAlert",
                "product_id": item.get("product_id"),
                "product_name": item.get("product_name"),
                "current_stock": stock,
                "reorder_threshold": threshold,
            }

            sqs.send_message(
                QueueUrl=NOTIFICATIONS_QUEUE_URL,
                MessageBody=json.dumps(message),
            )

            alerts_sent += 1

    result = {
        "items_checked": len(items),
        "alerts_sent": alerts_sent,
    }

    print(json.dumps({"event": "low_stock_check_complete", **result}))

    return {
        "statusCode": 200,
        "body": json.dumps(result),
    }
