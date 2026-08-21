from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


# ============================================================
# HEALTH CHECK
# ============================================================

def test_health_check():

    response = client.get(
        "/api/v1/health"
    )

    assert response.status_code == 200

    assert response.json()["status"] in [
        "healthy",
        "degraded"
    ]


# ============================================================
# AUTHENTICATION TESTS
# ============================================================

def test_get_inventory_without_token():

    response = client.get(
        "/api/v1/inventory"
    )

    assert response.status_code == 401


def test_get_inventory_item_without_token():

    response = client.get(
        "/api/v1/inventory/some-product-id"
    )

    assert response.status_code == 401


def test_update_inventory_without_token():

    response = client.put(
        "/api/v1/inventory/some-product-id",
        json={
            "stock_quantity": 100
        }
    )

    assert response.status_code == 401


def test_deduct_stock_without_token():

    response = client.post(
        "/api/v1/inventory/deduct",
        json={
            "product_id": "some-product-id",
            "quantity": 1,
            "order_id": "some-order-id"
        }
    )

    assert response.status_code == 401