import pytest
from fastapi.testclient import TestClient

class TestIntegrationFlows:
    def test_full_user_flow(self, client):
        """Test complete user flow: register -> login -> profile -> update -> logout"""
        # 1. Register
        register_response = client.post("/api/v1/users/register", json={
            "name": "Integration User",
            "email": "integration@example.com",
            "password": "IntegratePass123!"
        })
        assert register_response.status_code == 201
        
        # 2. Login
        login_response = client.post("/api/v1/users/login", json={
            "email": "integration@example.com",
            "password": "IntegratePass123!"
        })
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # 3. Get profile
        profile_response = client.get("/api/v1/users/profile", headers=headers)
        assert profile_response.status_code == 200
        user_id = profile_response.json()["id"]
        
        # 4. Update profile
        update_response = client.put("/api/v1/users/profile", 
            headers=headers,
            json={
                "name": "Updated Integration User"
            }
        )
        assert update_response.status_code == 200
        assert update_response.json()["name"] == "Updated Integration User"
        
        # 5. Logout
        logout_response = client.post("/api/v1/users/logout", headers=headers)
        assert logout_response.status_code == 200
        
        # 6. Try to access profile after logout (should fail - token still valid)
        # Note: With JWT, logout doesn't invalidate token server-side
        # This test just confirms the endpoint works

    def test_admin_full_flow(self, client, test_admin):
        """Test complete admin flow: login -> get user -> delete user"""
        # 1. Login as admin
        login_response = client.post("/api/v1/users/login", json={
            "email": "admin@example.com",
            "password": "AdminPassword123!"
        })
        assert login_response.status_code == 200
        admin_token = login_response.json()["access_token"]
        admin_headers = {"Authorization": f"Bearer {admin_token}"}
        
        # 2. Create a regular user
        register_response = client.post("/api/v1/users/register", json={
            "name": "Admin Test User",
            "email": "admintest@example.com",
            "password": "AdminTest123!"
        })
        assert register_response.status_code == 201
        user_id = register_response.json()["id"]
        
        # 3. Admin gets user details
        get_response = client.get(
            f"/api/v1/users/{user_id}",
            headers=admin_headers
        )
        assert get_response.status_code == 200
        
        # 4. Admin deletes user
        delete_response = client.delete(
            f"/api/v1/users/{user_id}",
            headers=admin_headers
        )
        assert delete_response.status_code == 204
        
        # 5. Verify user is deleted
        get_again_response = client.get(
            f"/api/v1/users/{user_id}",
            headers=admin_headers
        )
        assert get_again_response.status_code == 404

    def test_token_refresh_flow(self, client):
        """Test complete token refresh flow"""
        # 1. Register and login
        client.post("/api/v1/users/register", json={
            "name": "Refresh Flow User",
            "email": "refreshflow@example.com",
            "password": "RefreshPass123!"
        })
        
        login_response = client.post("/api/v1/users/login", json={
            "email": "refreshflow@example.com",
            "password": "RefreshPass123!"
        })
        assert login_response.status_code == 200
        refresh_token = login_response.json()["refresh_token"]
        
        # 2. Refresh token
        refresh_response = client.post("/api/v1/users/refresh", json={
            "refresh_token": refresh_token
        })
        assert refresh_response.status_code == 200
        new_access_token = refresh_response.json()["access_token"]
        
        # 3. Use new token
        headers = {"Authorization": f"Bearer {new_access_token}"}
        profile_response = client.get("/api/v1/users/profile", headers=headers)
        assert profile_response.status_code == 200