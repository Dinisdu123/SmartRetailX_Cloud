import pytest
from fastapi.testclient import TestClient

class TestRefreshToken:
    def test_refresh_success(self, client, test_user, refresh_token):
        """Test successful token refresh"""
        response = client.post("/api/v1/users/refresh", json={
            "refresh_token": refresh_token
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    def test_refresh_with_invalid_token(self, client):
        """Test refresh with invalid refresh token"""
        response = client.post("/api/v1/users/refresh", json={
            "refresh_token": "invalid.token.here"
        })
        assert response.status_code == 401

    def test_refresh_with_access_token(self, client, test_user):
        """Test refresh with access token instead of refresh token"""
        response = client.post("/api/v1/users/login", json={
            "email": "test@example.com",
            "password": "TestPassword123!"
        })
        access_token = response.json()["access_token"]
        
        response = client.post("/api/v1/users/refresh", json={
            "refresh_token": access_token
        })
        assert response.status_code == 401

    def test_refresh_for_deleted_user(self, client, test_user, test_admin):
        """Test refresh for deleted user fails"""
        # First login to get tokens
        login_response = client.post("/api/v1/users/login", json={
            "email": "test@example.com",
            "password": "TestPassword123!"
        })
        refresh_token = login_response.json()["refresh_token"]
        
        # Login as admin
        admin_login = client.post("/api/v1/users/login", json={
            "email": "admin@example.com",
            "password": "AdminPassword123!"
        })
        admin_token = admin_login.json()["access_token"]
        
        # Delete user (soft delete)
        client.delete(
            f"/api/v1/users/{test_user.id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        # Try to refresh
        response = client.post("/api/v1/users/refresh", json={
            "refresh_token": refresh_token
        })
        assert response.status_code == 401

    def test_refresh_missing_token(self, client):
        """Test refresh without token"""
        response = client.post("/api/v1/users/refresh", json={})
        assert response.status_code == 422