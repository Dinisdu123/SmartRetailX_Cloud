import requests
import pytest
import uuid
import time


# ============================================================
# SERVICE BASE URLS
# ============================================================

BASE_USER = "http://127.0.0.1:8001"
BASE_PRODUCT = "http://127.0.0.1:8002"
BASE_ORDER = "http://127.0.0.1:8003"
BASE_INVENTORY = "http://127.0.0.1:8004"


# ============================================================
# TEST DATA
# ============================================================

ADMIN_TOKEN = "YOUR_ADMIN_TOKEN_HERE"
CUSTOMER_TOKEN = "YOUR_CUSTOMER_TOKEN_HERE"


# ============================================================
# HEALTH CHECKS
# ============================================================

def test_all_services_health():
    services = [
        (BASE_USER, "user-management-service"),
        (BASE_PRODUCT, "product-catalogue-service"),
        (BASE_ORDER, "order-processing-service"),
        (BASE_INVENTORY, "inventory-management-service"),
    ]

    for base_url, service_name in services:
        response = requests.get(
            f"{base_url}/api/v1/health",
            timeout=10
        )

        assert response.status_code == 200, (
            f"{service_name} health check failed"
        )

        data = response.json()

        assert data["status"] in ["healthy", "degraded"], (
            f"{service_name} returned invalid health status"
        )


# ============================================================
# USER MANAGEMENT
# ============================================================

def test_user_management_health():
    response = requests.get(
        f"{BASE_USER}/api/v1/health",
        timeout=10
    )

    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


# ============================================================
# PRODUCT CATALOGUE
# ============================================================

def test_product_catalogue_health():
    response = requests.get(
        f"{BASE_PRODUCT}/api/v1/health",
        timeout=10
    )

    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


# ============================================================
# ORDER PROCESSING
# ============================================================

def test_order_processing_health():
    response = requests.get(
        f"{BASE_ORDER}/api/v1/health",
        timeout=10
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] in ["healthy", "degraded"]


# ============================================================
# INVENTORY MANAGEMENT
# ============================================================

def test_inventory_management_health():
    response = requests.get(
        f"{BASE_INVENTORY}/api/v1/health",
        timeout=10
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] in ["healthy", "degraded"]


# ============================================================
# AUTHENTICATION / RBAC
# ============================================================

def test_customer_cannot_access_inventory():
    response = requests.get(
        f"{BASE_INVENTORY}/api/v1/inventory",
        headers={
            "Authorization": f"Bearer {CUSTOMER_TOKEN}"
        },
        timeout=10
    )

    assert response.status_code == 403


def test_customer_cannot_update_inventory():
    response = requests.put(
        f"{BASE_INVENTORY}/api/v1/inventory/some-product-id",
        headers={
            "Authorization": f"Bearer {CUSTOMER_TOKEN}"
        },
        json={
            "stock_quantity": 100
        },
        timeout=10
    )

    assert response.status_code == 403


def test_customer_cannot_deduct_inventory():
    response = requests.post(
        f"{BASE_INVENTORY}/api/v1/inventory/deduct",
        headers={
            "Authorization": f"Bearer {CUSTOMER_TOKEN}"
        },
        json={
            "product_id": "some-product-id",
            "quantity": 1,
            "order_id": "some-order-id"
        },
        timeout=10
    )

    assert response.status_code == 403


# ============================================================
# INVENTORY OPERATIONS
# ============================================================

def test_admin_can_get_inventory():
    response = requests.get(
        f"{BASE_INVENTORY}/api/v1/inventory",
        headers={
            "Authorization": f"Bearer {ADMIN_TOKEN}"
        },
        timeout=10
    )

    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_admin_can_get_inventory_item():
    product_id = "HEADPHONES-001"

    response = requests.get(
        f"{BASE_INVENTORY}/api/v1/inventory/{product_id}",
        headers={
            "Authorization": f"Bearer {ADMIN_TOKEN}"
        },
        timeout=10
    )

    assert response.status_code == 200

    data = response.json()

    assert data["product_id"] == product_id
    assert "stock_quantity" in data


# ============================================================
# ORDER CREATION
# ============================================================

def test_create_order_without_token():
    response = requests.post(
        f"{BASE_ORDER}/api/v1/orders",
        json={
            "product_id": "HEADPHONES-001",
            "quantity": 1,
            "total_price": 99.99,
            "shipping_address": "123 Test Street"
        },
        timeout=10
    )

    assert response.status_code == 401


def test_get_orders_without_token():
    response = requests.get(
        f"{BASE_ORDER}/api/v1/orders",
        timeout=10
    )

    assert response.status_code == 401


# ============================================================
# END-TO-END ORDER FLOW
# ============================================================

def test_order_end_to_end():
    """
    Complete order flow:

    1. Check product exists
    2. Check inventory before order
    3. Create order
    4. Verify order was created
    5. Wait for inventory event processing
    6. Verify inventory was reduced
    """

    product_id = "HEADPHONES-001"
    quantity = 1

    headers = {
        "Authorization": f"Bearer {CUSTOMER_TOKEN}"
    }

    admin_headers = {
        "Authorization": f"Bearer {ADMIN_TOKEN}"
    }

    # --------------------------------------------------------
    # Step 1 — Check product
    # --------------------------------------------------------

    product_response = requests.get(
        f"{BASE_PRODUCT}/api/v1/products/{product_id}",
        headers=headers,
        timeout=10
    )

    assert product_response.status_code == 200, (
        "Step 1 Failed: Product not found"
    )

    product = product_response.json()

    # --------------------------------------------------------
    # Step 2 — Check inventory before order
    # --------------------------------------------------------

    inventory_response = requests.get(
        f"{BASE_INVENTORY}/api/v1/inventory/{product_id}",
        headers=admin_headers,
        timeout=10
    )

    assert inventory_response.status_code == 200, (
        "Step 2 Failed: Inventory item not found"
    )

    inventory_before = inventory_response.json()

    stock_before = inventory_before["stock_quantity"]

    assert stock_before >= quantity, (
        f"Step 2 Failed: Insufficient stock. "
        f"Available={stock_before}, Required={quantity}"
    )

    # --------------------------------------------------------
    # Step 3 — Create order
    # --------------------------------------------------------

    order_data = {
        "product_id": product_id,
        "quantity": quantity,
        "total_price": float(product.get("price", 99.99)) * quantity,
        "shipping_address": "123 Test Street, Colombo"
    }

    order_response = requests.post(
        f"{BASE_ORDER}/api/v1/orders",
        headers=headers,
        json=order_data,
        timeout=10
    )

    assert order_response.status_code in [200, 201], (
        f"Step 3 Failed: Order creation returned "
        f"{order_response.status_code}: {order_response.text}"
    )

    order = order_response.json()

    order_id = order["id"]

    assert order_id is not None

    # --------------------------------------------------------
    # Step 4 — Verify order
    # --------------------------------------------------------

    get_order_response = requests.get(
        f"{BASE_ORDER}/api/v1/orders/{order_id}",
        headers=headers,
        timeout=10
    )

    assert get_order_response.status_code == 200, (
        "Step 4 Failed: Could not retrieve created order"
    )

    created_order = get_order_response.json()

    assert created_order["id"] == order_id
    assert created_order["product_id"] == product_id
    assert created_order["quantity"] == quantity

    # --------------------------------------------------------
    # Step 5 — Wait for inventory event processing
    # --------------------------------------------------------

    time.sleep(3)

    # --------------------------------------------------------
    # Step 6 — Verify inventory was reduced
    # --------------------------------------------------------

    inventory_after_response = requests.get(
        f"{BASE_INVENTORY}/api/v1/inventory/{product_id}",
        headers=admin_headers,
        timeout=10
    )

    assert inventory_after_response.status_code == 200, (
        "Step 6 Failed: Could not retrieve updated inventory"
    )

    inventory_after = inventory_after_response.json()

    stock_after = inventory_after["stock_quantity"]

    assert stock_after == stock_before - quantity, (
        f"Step 6 Failed: Inventory was not correctly reduced. "
        f"Before={stock_before}, After={stock_after}, "
        f"Expected={stock_before - quantity}"
    )

    print(
        f"\n✅ E2E Test Complete — "
        f"Order {order_id} successfully created "
        f"and inventory updated"
    )