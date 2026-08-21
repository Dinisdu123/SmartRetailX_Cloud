"""
SQS consumer for inventory-management-service.

Listens to the orders queue for OrderPlaced events and automatically
deducts stock from the inventory table. If stock cannot be reserved
(missing inventory record, or insufficient quantity), a compensating
event is published to the notifications queue instead of silently
failing or allowing stock to go negative -- this is the compensating
action half of the Saga pattern referenced in the technical report.
"""

import json
import logging
import os
import threading
from datetime import datetime, timezone

import boto3

from app.database import get_inventory_table


logger = logging.getLogger("inventory-management-service")

AWS_REGION = os.getenv("AWS_REGION", "ap-south-1")
ORDERS_QUEUE_URL = os.getenv("SQS_ORDERS_QUEUE_URL")
NOTIFICATIONS_QUEUE_URL = os.getenv("SQS_NOTIFICATIONS_QUEUE_URL")

_stop_event = threading.Event()


# ============================================================
# SQS CLIENT
# ============================================================

def get_sqs_client():
    return boto3.client("sqs", region_name=AWS_REGION)


# ============================================================
# COMPENSATING EVENT (Saga pattern)
# ============================================================

def publish_compensation_event(event_type: str, payload: dict):
    """
    Publish a compensating event when a saga step cannot complete
    (e.g. insufficient stock). This lets the rest of the platform
    react -- for example, showing a failure in the admin
    notifications view, or (in a future iteration) triggering an
    automatic order cancellation in order-processing-service.
    """

    if not NOTIFICATIONS_QUEUE_URL:
        logger.warning(
            "SQS_NOTIFICATIONS_QUEUE_URL not configured; "
            "skipping compensation event"
        )
        return

    sqs = get_sqs_client()

    message = {
        "event_type": event_type,
        **payload,
    }

    try:
        sqs.send_message(
            QueueUrl=NOTIFICATIONS_QUEUE_URL,
            MessageBody=json.dumps(message),
        )

        logger.info(json.dumps({
            "service": "inventory-management-service",
            "event": "compensation_event_published",
            "compensation_event_type": event_type,
            "order_id": payload.get("order_id"),
        }))

    except Exception as exc:
        logger.error(json.dumps({
            "service": "inventory-management-service",
            "event": "compensation_event_publish_failed",
            "error": str(exc),
        }))


# ============================================================
# ORDER EVENT HANDLING
# ============================================================

def handle_order_placed(message_body: dict):
    """
    Deduct stock for an OrderPlaced event. Publishes a
    StockReservationFailed compensating event instead of failing
    silently if the product has no inventory record or insufficient
    stock -- this prevents stock from ever going negative.
    """

    product_id = message_body.get("product_id")
    quantity = message_body.get("quantity")
    order_id = message_body.get("order_id")
    user_id = message_body.get("user_id")

    if not product_id or quantity is None:
        logger.warning(json.dumps({
            "service": "inventory-management-service",
            "event": "order_event_missing_fields",
            "message_body": message_body,
        }))
        return

    table = get_inventory_table()

    response = table.get_item(Key={"product_id": product_id})
    item = response.get("Item")

    if not item:
        logger.warning(json.dumps({
            "service": "inventory-management-service",
            "event": "inventory_record_missing",
            "product_id": product_id,
            "order_id": order_id,
        }))

        publish_compensation_event("StockReservationFailed", {
            "order_id": order_id,
            "user_id": user_id,
            "product_id": product_id,
            "reason": "No inventory record found for product",
        })
        return

    current_stock = int(item.get("stock_quantity", 0))

    if current_stock < quantity:
        logger.warning(json.dumps({
            "service": "inventory-management-service",
            "event": "insufficient_stock",
            "product_id": product_id,
            "order_id": order_id,
            "available": current_stock,
            "requested": quantity,
        }))

        publish_compensation_event("StockReservationFailed", {
            "order_id": order_id,
            "user_id": user_id,
            "product_id": product_id,
            "available_stock": current_stock,
            "requested_quantity": quantity,
            "reason": "Insufficient stock at time of fulfillment",
        })
        return

    new_stock = current_stock - quantity

    item["stock_quantity"] = new_stock
    item["updated_at"] = datetime.now(timezone.utc).isoformat()

    table.put_item(Item=item)

    logger.info(json.dumps({
        "service": "inventory-management-service",
        "event": "stock_auto_deducted",
        "product_id": product_id,
        "order_id": order_id,
        "quantity_deducted": quantity,
        "remaining_stock": new_stock,
    }))


def process_message(message: dict):
    try:
        body = json.loads(message["Body"])
    except (KeyError, json.JSONDecodeError) as exc:
        logger.error(f"Failed to parse SQS message body: {exc}")
        return

    event_type = body.get("event_type")

    if event_type == "OrderPlaced":
        handle_order_placed(body)
    else:
        # Not an event this consumer acts on (e.g. OrderCancelled,
        # OrderShipped) -- acknowledged and skipped.
        logger.info(json.dumps({
            "service": "inventory-management-service",
            "event": "order_event_ignored",
            "event_type": event_type,
        }))


# ============================================================
# POLLING LOOP
# ============================================================

def consume_loop():
    """
    Long-polls the orders queue for new messages and processes them.
    Runs for the lifetime of the application in a background thread.
    """

    if not ORDERS_QUEUE_URL:
        logger.error(
            "SQS_ORDERS_QUEUE_URL not configured; "
            "SQS consumer will not start"
        )
        return

    sqs = get_sqs_client()

    logger.info(json.dumps({
        "service": "inventory-management-service",
        "event": "sqs_consumer_started",
        "queue_url": ORDERS_QUEUE_URL,
    }))

    while not _stop_event.is_set():
        try:
            response = sqs.receive_message(
                QueueUrl=ORDERS_QUEUE_URL,
                MaxNumberOfMessages=5,
                WaitTimeSeconds=20,  # long polling
                VisibilityTimeout=30,
            )

            messages = response.get("Messages", [])

            for message in messages:
                process_message(message)

                sqs.delete_message(
                    QueueUrl=ORDERS_QUEUE_URL,
                    ReceiptHandle=message["ReceiptHandle"],
                )

        except Exception as exc:
            logger.error(json.dumps({
                "service": "inventory-management-service",
                "event": "sqs_consumer_error",
                "error": str(exc),
            }))
            _stop_event.wait(5)  # brief backoff before retrying


def start_consumer_thread():
    thread = threading.Thread(target=consume_loop, daemon=True)
    thread.start()
    return thread


def stop_consumer():
    _stop_event.set()
