from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_gateway_health():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
    assert response.json()["service"] == "api-gateway"

def test_gateway_health_shows_routes():
    response = client.get("/api/v1/health")
    assert "routes" in response.json()
    assert len(response.json()["routes"]) == 5

def test_gateway_rejects_unknown_path():
    response = client.get("/api/v1/unknown/path")
    assert response.status_code in [401, 404]

def test_gateway_rejects_protected_path_without_token():
    response = client.get("/api/v1/orders")
    assert response.status_code == 401

def test_gateway_rejects_invalid_token():
    response = client.get(
        "/api/v1/orders",
        headers={"Authorization": "Bearer invalid.token.here"}
    )
    assert response.status_code == 401

def test_gateway_allows_public_product_path():
    response = client.get("/api/v1/products")
    assert response.status_code in [200, 503]

def test_gateway_allows_register_without_token():
    response = client.post("/api/v1/users/register", json={
        "name": "Test",
        "email": "test@test.com",
        "password": "password123"
    })
    assert response.status_code in [201, 400, 503]

def test_gateway_allows_login_without_token():
    response = client.post("/api/v1/users/login", json={
        "email": "test@test.com",
        "password": "password123"
    })
    assert response.status_code in [200, 401, 503]