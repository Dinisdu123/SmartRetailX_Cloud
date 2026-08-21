import pytest
from fastapi.testclient import TestClient

class TestLogout:
    def test_logout_success(self, client, test_user, auth_headers):
        """Test successful logout"""
        response = client.post("/api/v1/users/logout", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["message"] == "Successfully logged out"

    def test_logout_without_auth(self, client):
        """Test logout without authentication"""
        response = client.post("/api/v1/users/logout")
        # The endpoint doesn't check auth for logout (stateless JWT)
        assert response.status_code == 200
        assert response.json()["message"] == "Successfully logged out"

    def test_logout_with_invalid_token(self, client):
        """Test logout with invalid token"""
        response = client.post(
            "/api/v1/users/logout",
            headers={"Authorization": "Bearer invalid.token.here"}
        )
        # The endpoint doesn't validate the token for logout
        assert response.status_code == 200
        assert response.json()["message"] == "Successfully logged out"

    def test_logout_with_expired_token(self, client, test_user):
        """Test logout with expired token"""
        # Logout doesn't validate token
        response = client.post(
            "/api/v1/users/logout",
            headers={"Authorization": "Bearer expired.token.here"}
        )
        assert response.status_code == 200