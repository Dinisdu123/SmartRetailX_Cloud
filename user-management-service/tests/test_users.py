import pytest
from fastapi.testclient import TestClient
from uuid import uuid4

class TestGetProfile:
    def test_get_profile_success(self, client, test_user, auth_headers):
        """Test getting current user profile"""
        response = client.get("/api/v1/users/profile", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(test_user.id)
        assert data["email"] == test_user.email
        assert data["name"] == test_user.name
        assert data["role"] == "customer"
        assert data["is_active"] == True

    def test_get_profile_unauthenticated(self, client):
        """Test getting profile without authentication"""
        response = client.get("/api/v1/users/profile")
        assert response.status_code == 401

class TestUpdateProfile:
    def test_update_profile_success(self, client, test_user, auth_headers):
        """Test successful profile update"""
        response = client.put("/api/v1/users/profile", 
            headers=auth_headers,
            json={
                "name": "Updated Name",
                "email": "updated@example.com"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Name"
        assert data["email"] == "updated@example.com"

    def test_update_profile_partial(self, client, test_user, auth_headers):
        """Test partial profile update"""
        response = client.put("/api/v1/users/profile",
            headers=auth_headers,
            json={
                "name": "Only Name Updated"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Only Name Updated"
        assert data["email"] == test_user.email  # Unchanged

    def test_update_profile_duplicate_email(self, client, test_user, test_admin, auth_headers):
        """Test updating to email already in use"""
        response = client.put("/api/v1/users/profile",
            headers=auth_headers,
            json={
                "email": "admin@example.com"  # Already taken by admin
            }
        )
        assert response.status_code == 400
        assert response.json()["detail"] == "Email already in use by another account"

    def test_update_profile_unauthenticated(self, client):
        """Test updating profile without authentication"""
        response = client.put("/api/v1/users/profile", json={"name": "New Name"})
        assert response.status_code == 401

class TestGetUserById:
    def test_admin_get_user(self, client, test_user, admin_headers):
        """Test admin can get any user by ID"""
        response = client.get(
            f"/api/v1/users/{test_user.id}",
            headers=admin_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(test_user.id)
        assert data["email"] == test_user.email

    def test_regular_user_get_other_user(self, client, test_user, test_admin, auth_headers):
        """Test regular user cannot get other user's details"""
        response = client.get(
            f"/api/v1/users/{test_admin.id}",
            headers=auth_headers
        )
        assert response.status_code == 403

    def test_admin_get_nonexistent_user(self, client, admin_headers):
        """Test admin getting non-existent user"""
        fake_id = uuid4()
        response = client.get(
            f"/api/v1/users/{fake_id}",
            headers=admin_headers
        )
        assert response.status_code == 404

class TestDeleteUser:
    def test_admin_delete_user(self, client, test_user, admin_headers):
        """Test admin can delete a user"""
        response = client.delete(
            f"/api/v1/users/{test_user.id}",
            headers=admin_headers
        )
        assert response.status_code == 204

    def test_regular_user_delete_user(self, client, test_user, auth_headers):
        """Test regular user cannot delete users"""
        response = client.delete(
            f"/api/v1/users/{test_user.id}",
            headers=auth_headers
        )
        assert response.status_code == 403

    def test_admin_delete_inactive_user(self, client, test_inactive_user, admin_headers):
        """Test admin deleting already deleted user"""
        response = client.delete(
            f"/api/v1/users/{test_inactive_user.id}",
            headers=admin_headers
        )
        assert response.status_code == 400
        assert response.json()["detail"] == "User is already deleted"

    def test_admin_delete_nonexistent_user(self, client, admin_headers):
        """Test admin deleting non-existent user"""
        fake_id = uuid4()
        response = client.delete(
            f"/api/v1/users/{fake_id}",
            headers=admin_headers
        )
        assert response.status_code == 404