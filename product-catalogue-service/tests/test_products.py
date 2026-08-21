import pytest
from fastapi.testclient import TestClient
from app.main import app
import uuid
import jwt
from datetime import datetime, timedelta
from app.config.settings import settings

client = TestClient(app)

# Helper to create admin token (same as User Service)
def create_admin_token():
    payload = {
        "sub": "admin-id",
        "role": "admin",
        "type": "access",
        "iss": settings.JWT_ISSUER,
        "aud": settings.JWT_AUDIENCE,
        "jti": str(uuid.uuid4()),
        "iat": datetime.utcnow(),
        "exp": datetime.utcnow() + timedelta(hours=1)
    }
    token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return {"Authorization": f"Bearer {token}"}

def create_customer_token():
    payload = {
        "sub": "customer-id",
        "role": "customer",
        "type": "access",
        "iss": settings.JWT_ISSUER,
        "aud": settings.JWT_AUDIENCE,
        "jti": str(uuid.uuid4()),
        "iat": datetime.utcnow(),
        "exp": datetime.utcnow() + timedelta(hours=1)
    }
    token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return {"Authorization": f"Bearer {token}"}

def create_expired_token():
    payload = {
        "sub": "admin-id",
        "role": "admin",
        "type": "access",
        "iss": settings.JWT_ISSUER,
        "aud": settings.JWT_AUDIENCE,
        "jti": str(uuid.uuid4()),
        "iat": datetime.utcnow() - timedelta(hours=2),
        "exp": datetime.utcnow() - timedelta(hours=1)
    }
    token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return {"Authorization": f"Bearer {token}"}

class TestHealthCheck:
    def test_health_check(self, client):
        """Test health check endpoint"""
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "service" in data
        assert "database" in data
        assert "version" in data
        
    def test_root_endpoint(self, client):
        """Test root endpoint"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "service" in data
        assert "version" in data
        assert "documentation" in data

class TestProducts:
    def test_get_products_no_auth_required(self, client):
        """Test getting products without authentication"""
        response = client.get("/api/v1/products")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_get_products_with_category_filter(self, client):
        """Test filtering products by category"""
        response = client.get("/api/v1/products?category=Electronics")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_get_products_with_price_filter(self, client):
        """Test filtering products by price range"""
        response = client.get("/api/v1/products?minPrice=10&maxPrice=500")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_get_products_with_search_filter(self, client):
        """Test searching products by name"""
        response = client.get("/api/v1/products?search=laptop")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_get_product_not_found(self, client):
        """Test getting non-existent product"""
        response = client.get("/api/v1/products/nonexistent-product-id")
        assert response.status_code == 404

    def test_create_product_without_token(self, client):
        """Test creating product without authentication"""
        response = client.post("/api/v1/products", json={
            "name": "Test Product",
            "description": "Test description",
            "price": 99.99,
            "category": "Electronics",
            "stock_quantity": 10
        })
        assert response.status_code == 401

    def test_create_product_as_admin(self, client):
        """Test creating product as admin"""
        headers = create_admin_token()
        response = client.post("/api/v1/products",
            headers=headers,
            json={
                "name": "Admin Created Product",
                "description": "Created by admin",
                "price": 199.99,
                "category": "Electronics",
                "stock_quantity": 50,
                "image_url": "https://example.com/product.jpg"
            }
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Admin Created Product"
        assert data["price"] == 199.99
        assert "id" in data

    def test_create_product_as_customer(self, client):
        """Test creating product as customer (should fail)"""
        headers = create_customer_token()
        response = client.post("/api/v1/products",
            headers=headers,
            json={
                "name": "Customer Product",
                "description": "Created by customer",
                "price": 99.99,
                "category": "Electronics",
                "stock_quantity": 10
            }
        )
        assert response.status_code == 403

    def test_create_product_invalid_data(self, client):
        """Test creating product with invalid data"""
        headers = create_admin_token()
        # Negative price
        response = client.post("/api/v1/products",
            headers=headers,
            json={
                "name": "Invalid Product",
                "description": "Invalid description",
                "price": -10.00,
                "category": "Electronics",
                "stock_quantity": 10
            }
        )
        assert response.status_code == 422

        # Negative stock
        response = client.post("/api/v1/products",
            headers=headers,
            json={
                "name": "Invalid Product",
                "description": "Invalid description",
                "price": 10.00,
                "category": "Electronics",
                "stock_quantity": -5
            }
        )
        assert response.status_code == 422

        # Empty name
        response = client.post("/api/v1/products",
            headers=headers,
            json={
                "name": "",
                "description": "Invalid description",
                "price": 10.00,
                "category": "Electronics",
                "stock_quantity": 10
            }
        )
        assert response.status_code == 422

    def test_create_product_invalid_image_url(self, client):
        """Test creating product with invalid image URL"""
        headers = create_admin_token()
        response = client.post("/api/v1/products",
            headers=headers,
            json={
                "name": "Invalid URL Product",
                "description": "Test description",
                "price": 99.99,
                "category": "Electronics",
                "stock_quantity": 10,
                "image_url": "not-a-valid-url"
            }
        )
        assert response.status_code == 422

    def test_update_product_as_admin(self, client):
        """Test updating product as admin"""
        # First create a product
        headers = create_admin_token()
        create_response = client.post("/api/v1/products",
            headers=headers,
            json={
                "name": "Update Test Product",
                "description": "To be updated",
                "price": 99.99,
                "category": "Electronics",
                "stock_quantity": 10
            }
        )
        product_id = create_response.json()["id"]
        
        # Update the product
        response = client.put(f"/api/v1/products/{product_id}",
            headers=headers,
            json={
                "name": "Updated Name",
                "price": 149.99,
                "stock_quantity": 25
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Name"
        assert data["price"] == 149.99
        assert data["stock_quantity"] == 25

    def test_update_nonexistent_product(self, client):
        """Test updating non-existent product"""
        headers = create_admin_token()
        response = client.put("/api/v1/products/nonexistent-id",
            headers=headers,
            json={
                "name": "Updated Name",
                "price": 149.99
            }
        )
        assert response.status_code == 404

    def test_update_product_as_customer(self, client):
        """Test updating product as customer (should fail)"""
        headers = create_customer_token()
        response = client.put("/api/v1/products/some-id",
            headers=headers,
            json={
                "name": "Updated Name"
            }
        )
        assert response.status_code == 403

    def test_delete_product_as_admin(self, client):
        """Test deleting product as admin"""
        # First create a product
        headers = create_admin_token()
        create_response = client.post("/api/v1/products",
            headers=headers,
            json={
                "name": "Delete Test Product",
                "description": "To be deleted",
                "price": 99.99,
                "category": "Electronics",
                "stock_quantity": 10
            }
        )
        product_id = create_response.json()["id"]
        
        # Delete the product
        response = client.delete(f"/api/v1/products/{product_id}",
            headers=headers
        )
        assert response.status_code == 204

    def test_delete_nonexistent_product(self, client):
        """Test deleting non-existent product"""
        headers = create_admin_token()
        response = client.delete("/api/v1/products/nonexistent-id",
            headers=headers
        )
        assert response.status_code == 404

    def test_delete_product_as_customer(self, client):
        """Test deleting product as customer (should fail)"""
        headers = create_customer_token()
        response = client.delete("/api/v1/products/some-id",
            headers=headers
        )
        assert response.status_code == 403

class TestAuthentication:
    def test_expired_token(self, client):
        """Test accessing endpoint with expired token"""
        headers = create_expired_token()
        response = client.post("/api/v1/products",
            headers=headers,
            json={
                "name": "Expired Token",
                "description": "Should fail",
                "price": 99.99,
                "category": "Electronics",
                "stock_quantity": 10
            }
        )
        assert response.status_code == 401

    def test_invalid_token(self, client):
        """Test accessing endpoint with invalid token"""
        headers = {"Authorization": "Bearer invalid.token.here"}
        response = client.post("/api/v1/products",
            headers=headers,
            json={
                "name": "Invalid Token",
                "description": "Should fail",
                "price": 99.99,
                "category": "Electronics",
                "stock_quantity": 10
            }
        )
        assert response.status_code == 401

    def test_missing_token(self, client):
        """Test accessing endpoint without token"""
        response = client.post("/api/v1/products",
            json={
                "name": "Missing Token",
                "description": "Should fail",
                "price": 99.99,
                "category": "Electronics",
                "stock_quantity": 10
            }
        )
        assert response.status_code == 401

    def test_invalid_token_audience(self, client):
        """Test accessing endpoint with invalid audience"""
        # Create token with wrong audience
        payload = {
            "sub": "admin-id",
            "role": "admin",
            "type": "access",
            "iss": settings.JWT_ISSUER,
            "aud": "wrong-audience",
            "jti": str(uuid.uuid4()),
            "iat": datetime.utcnow(),
            "exp": datetime.utcnow() + timedelta(hours=1)
        }
        token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
        headers = {"Authorization": f"Bearer {token}"}
        
        response = client.post("/api/v1/products",
            headers=headers,
            json={
                "name": "Wrong Audience",
                "description": "Should fail",
                "price": 99.99,
                "category": "Electronics",
                "stock_quantity": 10
            }
        )
        assert response.status_code == 401

    def test_invalid_token_issuer(self, client):
        """Test accessing endpoint with invalid issuer"""
        # Create token with wrong issuer
        payload = {
            "sub": "admin-id",
            "role": "admin",
            "type": "access",
            "iss": "wrong-issuer",
            "aud": settings.JWT_AUDIENCE,
            "jti": str(uuid.uuid4()),
            "iat": datetime.utcnow(),
            "exp": datetime.utcnow() + timedelta(hours=1)
        }
        token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
        headers = {"Authorization": f"Bearer {token}"}
        
        response = client.post("/api/v1/products",
            headers=headers,
            json={
                "name": "Wrong Issuer",
                "description": "Should fail",
                "price": 99.99,
                "category": "Electronics",
                "stock_quantity": 10
            }
        )
        assert response.status_code == 401