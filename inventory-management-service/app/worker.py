import boto3
import json
import time
import logging

from datetime import datetime, timezone

from app.database import get_inventory_table
from app.config.settings import settings


logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(
    "inventory-worker"
)


# ============================================================
# SQS CLIENT
# ============================================================

def get_sqs_client():
    return boto3.client(
        "sqs",
        region_name=settings.AWS_REGION,
        endpoint_url=settings.SQS_ENDPOINT,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
    )


# ============================================================
# SNS CLIENT
# ============================================================

def get_sns_client():
    return boto3.client(
        "sns",
        region_name=settings.AWS_REGION,
        endpoint_url=settings.SNS_ENDPOINT,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
    )


# ============================================================
# PROCESS ORDER PLACED EVENT
# ============================================================

def process_order_placed(message: dict):
    product_id = message.get("product_id")
    quantity = message.get("quantity")
    order_id = message.get("order_id")

    if not product_id or not quantity or not order_id:
        logger.error(
            json.dumps({
                "service": "inventory-worker",
                "event": "invalid_order_event",
                "message": message
            })
        )

        return False

    quantity = int(quantity)

    table = get_inventory_table()

    response = table.get_item(
        Key={
            "product_id": product_id
        }
    )

    item = response.get("Item")

    if not item:
        logger.warning(
            json.dumps({
                "service": "inventory-worker",
                "event": "inventory_item_not_found",
                "product_id": product_id,
                "order_id": order_id
            })
        )

        return False

    current_stock = int(
        item.get("stock_quantity", 0)
    )

    # Do not allow negative inventory
    if current_stock < quantity:

        logger.warning(
            json.dumps({
                "service": "inventory-worker",
                "event": "insufficient_stock",
                "product_id": product_id,
                "order_id": order_id,
                "available_stock": current_stock,
                "requested_quantity": quantity
            })
        )

        return False

    new_stock = current_stock - quantity

    item["stock_quantity"] = new_stock

    item["updated_at"] = (
        datetime.now(timezone.utc).isoformat()
    )

    table.put_item(
        Item=item
    )

    logger.info(
        json.dumps({
            "service": "inventory-worker",
            "event": "stock_deducted",
            "product_id": product_id,
            "order_id": order_id,
            "quantity_deducted": quantity,
            "remaining_stock": new_stock
        })
    )

    # Check low-stock threshold
    reorder_threshold = int(
        item.get("reorder_threshold", 10)
    )

    if new_stock <= reorder_threshold:

        publish_low_stock_alert(
            product_id,
            new_stock,
            item.get(
                "product_name",
                "Unknown"
            )
        )

    return True


# ============================================================
# LOW STOCK ALERT
# ============================================================

def publish_low_stock_alert(
    product_id: str,
    stock: int,
    product_name: str
):
    notification_queue_url = (
        settings.NOTIFICATION_QUEUE_URL
    )

    try:

        sqs = get_sqs_client()

        message = {
            "event_type": "LowStockAlert",
            "product_id": product_id,
            "product_name": product_name,
            "current_stock": stock
        }

        sqs.send_message(
            QueueUrl=notification_queue_url,
            MessageBody=json.dumps(message)
        )

        logger.info(
            json.dumps({
                "service": "inventory-worker",
                "event": "low_stock_alert_published",
                "product_id": product_id,
                "stock": stock
            })
        )

    except Exception as e:

        logger.error(
            json.dumps({
                "service": "inventory-worker",
                "event": "low_stock_alert_failed",
                "product_id": product_id,
                "error": str(e)
            })
        )


# ============================================================
# START WORKER
# ============================================================

def start_worker():

    sqs = get_sqs_client()

    queue_url = settings.SQS_QUEUE_URL

    logger.info(
        json.dumps({
            "service": "inventory-worker",
            "event": "worker_started",
            "message": (
                "Listening for OrderPlaced events..."
            )
        })
    )

    while True:

        try:

            response = sqs.receive_message(
                QueueUrl=queue_url,
                MaxNumberOfMessages=10,
                WaitTimeSeconds=5
            )

            messages = response.get(
                "Messages",
                []
            )

            for msg in messages:

                try:

                    body = json.loads(
                        msg["Body"]
                    )

                    event_type = body.get(
                        "event_type"
                    )

                    logger.info(
                        json.dumps({
                            "service": "inventory-worker",
                            "event": "message_received",
                            "event_type": event_type
                        })
                    )

                    if event_type == "OrderPlaced":

                        process_order_placed(
                            body
                        )

                    else:

                        logger.info(
                            json.dumps({
                                "service": "inventory-worker",
                                "event": "event_ignored",
                                "event_type": event_type
                            })
                        )

                    # Delete only after processing
                    sqs.delete_message(
                        QueueUrl=queue_url,
                        ReceiptHandle=msg[
                            "ReceiptHandle"
                        ]
                    )

                    logger.info(
                        json.dumps({
                            "service": "inventory-worker",
                            "event": "message_deleted",
                            "message_id": msg[
                                "MessageId"
                            ]
                        })
                    )

                except Exception as e:

                    logger.error(
                        json.dumps({
                            "service": "inventory-worker",
                            "event": "message_processing_error",
                            "error": str(e)
                        })
                    )

        except Exception as e:

            logger.error(
                json.dumps({
                    "service": "inventory-worker",
                    "event": "receive_error",
                    "error": str(e)
                })
            )

            time.sleep(5)


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    start_worker()