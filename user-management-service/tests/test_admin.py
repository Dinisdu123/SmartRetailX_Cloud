import pytest
from fastapi.testclient import TestClient
from app.models import User, RoleEnum
import bcrypt
from uuid import uuid4

class TestAdminAccess:
    def test_admin_can_get_all_users(self, client, test_user, test_admin, admin_headers):
        """Test admin can get any user's details"""
        response = client.get(
            f"/api/v1/users/{test_user.id}",
            headers=admin_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(test_user.id)

    def test_non_admin_cannot_access_admin_endpoints(self, client, test_user, test_admin, auth_headers):
        """Test regular user cannot access admin endpoints"""
        response = client.get(
            f"/api/v1/users/{test_admin.id}",
            headers=auth_headers
        )
        assert response.status_code == 403

    def test_admin_can_delete_any_user(self, client, test_user, admin_headers):
        """Test admin can delete any user"""
        response = client.delete(
            f"/api/v1/users/{test_user.id}",
            headers=admin_headers
        )
        assert response.status_code == 204

    def test_admin_can_delete_multiple_users(self, client, db_session, admin_headers):
        """Test admin can delete multiple users"""
        # Create multiple users
        users = []
        for i in range(3):
            hashed = bcrypt.hashpw(f"password{i}".encode("utf-8"), bcrypt.gensalt())
            user = User(
                id=uuid4(),
                name=f"User {i}",
                email=f"user{i}@example.com",
                password_hash=hashed.decode("utf-8"),
                role=RoleEnum.customer,
                is_active=True
            )
            db_session.add(user)
            users.append(user)
        db_session.commit()
        
        # Delete each user
        for user in users:
            response = client.delete(
                f"/api/v1/users/{user.id}",
                headers=admin_headers
            )
            assert response.status_code == 204

    def test_admin_get_deleted_user(self, client, test_user, admin_headers):
        """Test admin cannot get deleted user"""
        # First delete user
        client.delete(
            f"/api/v1/users/{test_user.id}",
            headers=admin_headers
        )
        
        # Try to get deleted user
        response = client.get(
            f"/api/v1/users/{test_user.id}",
            headers=admin_headers
        )
        assert response.status_code == 404