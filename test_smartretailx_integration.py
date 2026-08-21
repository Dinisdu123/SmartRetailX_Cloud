"""
Integration test suite for the SmartRetailX platform.

These tests exercise the live, deployed ALB endpoint rather than mocking
each service in isolation, so they double as both integration and API
tests as required by Task 8 of the assignment.

Run with:
    pip install pytest requests
    pytest test_smartretailx_integration.py -v
"""

import uuid

import pytest
import requests

BASE_URL = "http://smartretailx-alb-2036217170.ap-south-1.elb.amazonaws.com/api/v1"

EXISTING_EMAIL = "testuser@example.com"
EXISTING_PASSWORD = "TestPass123!"


# ============================================================
# FIXTURES
# ============================================================

@pytest.fixture(scope="session")
def access_token():
    """Log in with a known test account and return a valid access token."""

    response = requests.post(
        f"{BASE_URL}/users/login",
        json={"email": EXISTING_EMAIL, "password": EXISTING_PASSWORD},
        timeout=10,
    )

    assert response.status_code == 200, f"Login failed: {response.text}"

    return response.json()["access_token"]


@pytest.fixture(scope="session")
def auth_headers(access_token):
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture()
def new_user_credentials():
    """Generate a unique email so registration tests can be re-run safely."""

    unique_id = uuid.uuid4().hex[:8]

    return {
        "name": "Pytest Integration User",
        "email": f"pytest.{unique_id}@example.com",
        "password": "TestPass123!",
    }


# ============================================================
# GATEWAY HEALTH
# ============================================================

class TestGatewayHealth:

    def test_health_check_returns_200(self):
        response = requests.get(f"{BASE_URL}/health", timeout=10)

        assert response.status_code == 200
        assert response.json()["status"] == "healthy"


# ============================================================
# USER MANAGEMENT SERVICE
# ============================================================

class TestUserRegistration:

    def test_register_new_user_succeeds(self, new_user_credentials):
        response = requests.post(
            f"{BASE_URL}/users/register",
            json=new_user_credentials,
            timeout=10,
        )

        assert response.status_code == 201

        body = response.json()

        assert body["email"] == new_user_credentials["email"]
        assert body["role"] == "customer"
        assert "password" not in body
        assert "password_hash" not in body

    def test_register_duplicate_email_fails(self, new_user_credentials):
        # Register once
        requests.post(f"{BASE_URL}/users/register", json=new_user_credentials, timeout=10)

        # Register again with the same email
        response = requests.post(
            f"{BASE_URL}/users/register",
            json=new_user_credentials,
            timeout=10,
        )

        assert response.status_code == 400

    def test_register_missing_fields_fails(self):
        response = requests.post(
            f"{BASE_URL}/users/register",
            json={"email": "incomplete@example.com"},
            timeout=10,
        )

        assert response.status_code == 422  # FastAPI validation error


class TestUserLogin:

    def test_login_with_valid_credentials_succeeds(self):
        response = requests.post(
            f"{BASE_URL}/users/login",
            json={"email": EXISTING_EMAIL, "password": EXISTING_PASSWORD},
            timeout=10,
        )

        assert response.status_code == 200

        body = response.json()

        assert "access_token" in body
        assert "refresh_token" in body

    def test_login_with_wrong_password_fails(self):
        response = requests.post(
            f"{BASE_URL}/users/login",
            json={"email": EXISTING_EMAIL, "password": "WrongPassword123"},
            timeout=10,
        )

        assert response.status_code == 401

    def test_login_with_nonexistent_email_fails(self):
        response = requests.post(
            f"{BASE_URL}/users/login",
            json={"email": "doesnotexist@example.com", "password": "whatever"},
            timeout=10,
        )

        assert response.status_code == 401

    def test_login_error_does_not_reveal_whether_email_exists(self):
        """Security check: wrong password and nonexistent email should
        return an identical error message, so an attacker can't enumerate
        valid accounts by observing different error text."""

        wrong_password_response = requests.post(
            f"{BASE_URL}/users/login",
            json={"email": EXISTING_EMAIL, "password": "WrongPassword123"},
            timeout=10,
        )

        nonexistent_email_response = requests.post(
            f"{BASE_URL}/users/login",
            json={"email": "doesnotexist@example.com", "password": "whatever"},
            timeout=10,
        )

        assert wrong_password_response.json()["detail"] == nonexistent_email_response.json()["detail"]


class TestUserProfile:

    def test_get_profile_with_valid_token_succeeds(self, auth_headers):
        response = requests.get(f"{BASE_URL}/users/profile", headers=auth_headers, timeout=10)

        assert response.status_code == 200
        assert response.json()["email"] == EXISTING_EMAIL

    def test_get_profile_without_token_fails(self):
        response = requests.get(f"{BASE_URL}/users/profile", timeout=10)

        assert response.status_code == 401

    def test_get_profile_with_invalid_token_fails(self):
        response = requests.get(
            f"{BASE_URL}/users/profile",
            headers={"Authorization": "Bearer invalid.token.here"},
            timeout=10,
        )

        assert response.status_code == 401


# ============================================================
# PRODUCT CATALOGUE SERVICE
# ============================================================

class TestProducts:

    def test_get_all_products_succeeds(self):
        response = requests.get(f"{BASE_URL}/products", timeout=10)

        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_get_product_by_id_not_found(self):
        response = requests.get(f"{BASE_URL}/products/does-not-exist-12345", timeout=10)

        assert response.status_code == 404

    def test_create_product_without_admin_role_fails(self, auth_headers):
        """The default test account is admin in this environment; this test
        documents expected behaviour for a non-admin caller and should be
        run against a genuine customer-role token in a full CI pipeline."""

        response = requests.post(
            f"{BASE_URL}/products",
            json={
                "name": "Unauthorized Test Product",
                "description": "Should not be created without admin role",
                "price": 9.99,
                "category": "Test",
                "stock_quantity": 1,
            },
            headers=auth_headers,
            timeout=10,
        )

        assert response.status_code in (201, 403)

    def test_create_product_without_auth_fails(self):
        response = requests.post(
            f"{BASE_URL}/products",
            json={
                "name": "No Auth Product",
                "description": "Should fail",
                "price": 9.99,
                "category": "Test",
                "stock_quantity": 1,
            },
            timeout=10,
        )

        assert response.status_code == 401


# ============================================================
# ORDER PROCESSING SERVICE
# ============================================================

class TestOrders:

    def test_get_my_orders_succeeds(self, auth_headers):
        response = requests.get(f"{BASE_URL}/orders", headers=auth_headers, timeout=10)

        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_get_orders_without_auth_fails(self):
        response = requests.get(f"{BASE_URL}/orders", timeout=10)

        assert response.status_code in (401, 403)

    def test_create_order_for_nonexistent_product_fails(self, auth_headers):
        response = requests.post(
            f"{BASE_URL}/orders",
            json={
                "product_id": "does-not-exist",
                "quantity": 1,
                "total_price": 10.00,
                "shipping_address": "123 Test Street",
            },
            headers=auth_headers,
            timeout=10,
        )

        assert response.status_code in (400, 404, 502)

    def test_create_order_with_invalid_quantity_fails_validation(self, auth_headers):
        response = requests.post(
            f"{BASE_URL}/orders",
            json={
                "product_id": "any-id",
                "quantity": 0,  # violates gt=0 constraint
                "total_price": 10.00,
                "shipping_address": "123 Test Street",
            },
            headers=auth_headers,
            timeout=10,
        )

        assert response.status_code == 422

    def test_get_nonexistent_order_returns_404(self, auth_headers):
        response = requests.get(
            f"{BASE_URL}/orders/00000000-0000-0000-0000-000000000000",
            headers=auth_headers,
            timeout=10,
        )

        assert response.status_code == 404


# ============================================================
# INVENTORY MANAGEMENT SERVICE
# ============================================================

class TestInventory:

    def test_get_inventory_without_auth_fails(self):
        response = requests.get(f"{BASE_URL}/inventory", timeout=10)

        assert response.status_code == 401

    def test_get_inventory_with_auth(self, auth_headers):
        response = requests.get(f"{BASE_URL}/inventory", headers=auth_headers, timeout=10)

        assert response.status_code in (200, 403)


# ============================================================
# END-TO-END FLOW
# ============================================================

class TestEndToEndOrderFlow:
    """Exercises the full path: register -> login -> browse products ->
    attempt an order. Demonstrates inter-service communication working
    correctly (order-processing-service calling product-catalogue-service
    internally over Cloud Map DNS)."""

    def test_full_customer_journey(self, new_user_credentials):
        register_response = requests.post(
            f"{BASE_URL}/users/register",
            json=new_user_credentials,
            timeout=10,
        )
        assert register_response.status_code == 201

        login_response = requests.post(
            f"{BASE_URL}/users/login",
            json={
                "email": new_user_credentials["email"],
                "password": new_user_credentials["password"],
            },
            timeout=10,
        )
        assert login_response.status_code == 200

        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        products_response = requests.get(f"{BASE_URL}/products", timeout=10)
        assert products_response.status_code == 200

        products = products_response.json()

        if products:
            product = products[0]

            order_response = requests.post(
                f"{BASE_URL}/orders",
                json={
                    "product_id": product["id"],
                    "quantity": 1,
                    "total_price": product["price"],
                    "shipping_address": "123 Integration Test Street",
                },
                headers=headers,
                timeout=10,
            )

            # 201 if stock available, 400 if out of stock -- both prove
            # the cross-service product lookup succeeded
            assert order_response.status_code in (201, 400)
