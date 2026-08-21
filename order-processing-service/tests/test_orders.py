from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health_check():

    response = client.get(
        "/api/v1/health"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["service"] == (
        "order-processing-service"
    )

    assert data["database"] in [
        "connected",
        "disconnected"
    ]

    assert data["sqs"] in [
        "connected",
        "disconnected"
    ]


def test_get_orders_without_token():

    response = client.get(
        "/api/v1/orders"
    )

    assert response.status_code == 401


def test_create_order_without_token():

    response = client.post(

        "/api/v1/orders",

        json={

            "product_id":
                "some-product-id",

            "quantity":
                1,

            "shipping_address":
                "123 Test Street"
        }
    )

    assert response.status_code == 401


def test_get_order_without_token():

    response = client.get(
        "/api/v1/orders/some-order-id"
    )

    assert response.status_code in [
        401,
        422
    ]


def test_update_order_status_without_token():

    response = client.put(

        "/api/v1/orders/"
        "some-order-id/status",

        json={
            "status": "CONFIRMED"
        }
    )

    assert response.status_code == 401


def test_cancel_order_without_token():

    response = client.delete(

        "/api/v1/orders/"
        "some-order-id"
    )

    assert response.status_code in [
        401,
        422
    ]