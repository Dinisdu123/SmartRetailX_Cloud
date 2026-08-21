from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status
)

from sqlalchemy.orm import Session

from app.database import get_db

from app.models import (
    Order,
    OrderStatus
)

from app.schemas import (
    OrderCreate,
    OrderStatusUpdate,
    OrderResponse
)

from app.middleware.auth import (
    verify_token,
    require_admin
)

from app.config.settings import settings

from typing import List

from uuid import UUID

from decimal import Decimal

import boto3
import json
import time
import logging
import requests


logger = logging.getLogger(
    "order-processing-service"
)


# ============================================================
# CIRCUIT BREAKER
# ============================================================

class CircuitBreaker:

    def __init__(
        self,
        failure_threshold=3,
        recovery_timeout=30
    ):

        self.failure_threshold = (
            failure_threshold
        )

        self.recovery_timeout = (
            recovery_timeout
        )

        self.failure_count = 0

        self.last_failure_time = None

        self.state = "CLOSED"


    def call(
        self,
        func,
        *args,
        **kwargs
    ):

        if self.state == "OPEN":

            elapsed = (
                time.time()
                - self.last_failure_time
            )

            if elapsed > self.recovery_timeout:

                self.state = "HALF-OPEN"

                logger.info(
                    "Circuit breaker HALF-OPEN"
                )

            else:

                raise Exception(
                    "Circuit breaker is OPEN"
                )


        try:

            result = func(
                *args,
                **kwargs
            )

            if self.state == "HALF-OPEN":

                self.state = "CLOSED"

                self.failure_count = 0

                logger.info(
                    "Circuit breaker CLOSED"
                )

            return result


        except Exception as exc:

            self.failure_count += 1

            self.last_failure_time = (
                time.time()
            )

            if (
                self.failure_count
                >= self.failure_threshold
            ):

                self.state = "OPEN"

                logger.error(
                    "Circuit breaker OPEN"
                )

            raise exc


sqs_circuit_breaker = CircuitBreaker(

    failure_threshold=(
        settings.CIRCUIT_BREAKER_FAILURE_THRESHOLD
    ),

    recovery_timeout=(
        settings.CIRCUIT_BREAKER_RECOVERY_TIMEOUT
    )
)


# ============================================================
# ROUTER
# ============================================================

router = APIRouter(
    prefix="/api/v1/orders",
    tags=["Orders"]
)


# ============================================================
# SQS CLIENT
# ============================================================

def get_sqs_client():

    kwargs = {
        "region_name":
            settings.AWS_REGION
    }

    if settings.SQS_ENDPOINT:

        kwargs["endpoint_url"] = (
            settings.SQS_ENDPOINT
        )

        kwargs["aws_access_key_id"] = (
            settings.AWS_ACCESS_KEY_ID
        )

        kwargs["aws_secret_access_key"] = (
            settings.AWS_SECRET_ACCESS_KEY
        )

    return boto3.client(
        "sqs",
        **kwargs
    )


# ============================================================
# SQS MESSAGE
# ============================================================

def _send_sqs_message(
    queue_url: str,
    message: dict
):

    sqs = get_sqs_client()

    return sqs.send_message(
        QueueUrl=queue_url,
        MessageBody=json.dumps(
            message
        )
    )


def publish_order_event(
    event_type: str,
    order_id: str,
    user_id: str,
    product_id: str,
    quantity: int
):

    message = {

        "event_type":
            event_type,

        "order_id":
            order_id,

        "user_id":
            user_id,

        "product_id":
            product_id,

        "quantity":
            quantity
    }


    for attempt in range(3):

        try:

            response = (
                sqs_circuit_breaker.call(
                    _send_sqs_message,
                    settings.SQS_QUEUE_URL,
                    message
                )
            )

            logger.info(
                json.dumps({

                    "event":
                        "order_event_published",

                    "event_type":
                        event_type,

                    "order_id":
                        order_id,

                    "message_id":
                        response["MessageId"],

                    "attempt":
                        attempt + 1
                })
            )

            return True


        except Exception as exc:

            logger.warning(
                json.dumps({

                    "event":
                        "order_event_publish_failed",

                    "event_type":
                        event_type,

                    "order_id":
                        order_id,

                    "attempt":
                        attempt + 1,

                    "error":
                        str(exc)
                })
            )

            if (
                attempt < 2
                and "Circuit breaker is OPEN"
                not in str(exc)
            ):

                time.sleep(
                    2 ** attempt
                )

            else:

                break


    return False


# ============================================================
# PRODUCT SERVICE
# ============================================================

def get_product(product_id: str):

    url = (
        f"{settings.PRODUCT_SERVICE_URL}"
        f"/api/v1/products/{product_id}"
    )

    response = requests.get(
        url,
        timeout=5
    )

    if response.status_code == 404:

        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    if response.status_code != 200:

        raise HTTPException(
            status_code=502,
            detail="Product Catalogue Service unavailable"
        )

    return response.json()


# ============================================================
# CREATE ORDER
# ============================================================

@router.post(
    "",
    response_model=OrderResponse,
    status_code=status.HTTP_201_CREATED
)
def create_order(

    order: OrderCreate,

    db: Session = Depends(get_db),

    token: dict = Depends(verify_token)
):

    try:

        # --------------------------------------------
        # Get product information
        # --------------------------------------------

        product = get_product(
            order.product_id
        )

        # --------------------------------------------
        # Check stock
        # --------------------------------------------

        stock = int(
            product.get(
                "stock_quantity",
                0
            )
        )

        if order.quantity > stock:

            raise HTTPException(
                status_code=400,
                detail=(
                    "Insufficient product stock"
                )
            )

        # --------------------------------------------
        # Calculate total price
        # --------------------------------------------

        unit_price = Decimal(
            str(product["price"])
        )

        total_price = (
            unit_price
            * order.quantity
        )

        # --------------------------------------------
        # Create order
        # --------------------------------------------

        new_order = Order(

            user_id=UUID(
                token["sub"]
            ),

            product_id=order.product_id,

            quantity=order.quantity,

            total_price=total_price,

            shipping_address=(
                order.shipping_address
            ),

            status=OrderStatus.PENDING
        )

        db.add(new_order)

        db.commit()

        db.refresh(new_order)

        # --------------------------------------------
        # Publish event
        # --------------------------------------------

        published = publish_order_event(

            "OrderPlaced",

            str(new_order.id),

            str(new_order.user_id),

            new_order.product_id,

            new_order.quantity
        )

        logger.info(
            json.dumps({

                "event":
                    "order_created",

                "order_id":
                    str(new_order.id),

                "event_published":
                    published
            })
        )

        return new_order


    except HTTPException:

        db.rollback()

        raise


    except Exception as exc:

        db.rollback()

        logger.error(
            json.dumps({

                "event":
                    "order_creation_failed",

                "error":
                    str(exc)
            })
        )

        raise HTTPException(
            status_code=500,
            detail="Failed to create order"
        )


# ============================================================
# GET ORDERS
# ============================================================

@router.get(
    "",
    response_model=List[OrderResponse]
)
def get_orders(

    db: Session = Depends(get_db),

    token: dict = Depends(verify_token)
):

    if token.get("role") == "admin":

        return db.query(
            Order
        ).order_by(
            Order.created_at.desc()
        ).all()


    return db.query(
        Order
    ).filter(
        Order.user_id == UUID(
            token["sub"]
        )
    ).order_by(
        Order.created_at.desc()
    ).all()


# ============================================================
# GET ORDER BY ID
# ============================================================

@router.get(
    "/{order_id}",
    response_model=OrderResponse
)
def get_order(

    order_id: UUID,

    db: Session = Depends(get_db),

    token: dict = Depends(verify_token)
):

    order = db.query(
        Order
    ).filter(
        Order.id == order_id
    ).first()


    if not order:

        raise HTTPException(
            status_code=404,
            detail="Order not found"
        )


    if (
        token.get("role") != "admin"
        and str(order.user_id)
        != token["sub"]
    ):

        raise HTTPException(
            status_code=403,
            detail="Access denied"
        )


    return order


# ============================================================
# UPDATE ORDER STATUS
# ============================================================

@router.put(
    "/{order_id}/status",
    response_model=OrderResponse
)
def update_order_status(

    order_id: UUID,

    status_update: OrderStatusUpdate,

    db: Session = Depends(get_db),

    token: dict = Depends(require_admin)
):

    order = db.query(
        Order
    ).filter(
        Order.id == order_id
    ).first()


    if not order:

        raise HTTPException(
            status_code=404,
            detail="Order not found"
        )


    current_status = order.status

    new_status = (
        status_update.status
    )


    allowed_transitions = {

        OrderStatus.PENDING: [
            OrderStatus.CONFIRMED,
            OrderStatus.CANCELLED
        ],

        OrderStatus.CONFIRMED: [
            OrderStatus.SHIPPED,
            OrderStatus.CANCELLED
        ],

        OrderStatus.SHIPPED: [
            OrderStatus.DELIVERED
        ],

        OrderStatus.DELIVERED: [],

        OrderStatus.CANCELLED: []
    }


    if (
        new_status
        not in allowed_transitions[
            current_status
        ]
    ):

        raise HTTPException(
            status_code=400,
            detail=(
                f"Cannot change order status "
                f"from {current_status.value} "
                f"to {new_status.value}"
            )
        )


    order.status = new_status

    db.commit()

    db.refresh(order)


    publish_order_event(

        f"Order{new_status.value.title()}",

        str(order.id),

        str(order.user_id),

        order.product_id,

        order.quantity
    )


    return order


# ============================================================
# CANCEL ORDER
# ============================================================

@router.delete(
    "/{order_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
def cancel_order(

    order_id: UUID,

    db: Session = Depends(get_db),

    token: dict = Depends(verify_token)
):

    order = db.query(
        Order
    ).filter(
        Order.id == order_id
    ).first()


    if not order:

        raise HTTPException(
            status_code=404,
            detail="Order not found"
        )


    if (
        token.get("role") != "admin"
        and str(order.user_id)
        != token["sub"]
    ):

        raise HTTPException(
            status_code=403,
            detail="Access denied"
        )


    if order.status not in [

        OrderStatus.PENDING,

        OrderStatus.CONFIRMED

    ]:

        raise HTTPException(

            status_code=400,

            detail=(
                "Only PENDING or CONFIRMED "
                "orders can be cancelled"
            )
        )


    order.status = (
        OrderStatus.CANCELLED
    )

    db.commit()


    publish_order_event(

        "OrderCancelled",

        str(order.id),

        str(order.user_id),

        order.product_id,

        order.quantity
    )


    return None