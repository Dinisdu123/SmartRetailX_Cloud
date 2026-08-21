import pytest
from fastapi.testclient import TestClient
from app.schemas import UserRegister
from pydantic import ValidationError

class TestPasswordValidation:
    def test_password_too_short(self):
        """Test password shorter than 8 characters"""
        with pytest.raises(ValidationError) as exc_info:
            UserRegister(
                name="Test User",
                email="test@example.com",
                password="Short1!"
            )
        assert "at least 8 characters" in str(exc_info.value)

    def test_password_no_uppercase(self):
        """Test password without uppercase letter"""
        with pytest.raises(ValidationError) as exc_info:
            UserRegister(
                name="Test User",
                email="test@example.com",
                password="lowercase123!"
            )
        assert "uppercase" in str(exc_info.value)

    def test_password_no_lowercase(self):
        """Test password without lowercase letter"""
        with pytest.raises(ValidationError) as exc_info:
            UserRegister(
                name="Test User",
                email="test@example.com",
                password="UPPERCASE123!"
            )
        assert "lowercase" in str(exc_info.value)

    def test_password_no_digit(self):
        """Test password without digit"""
        with pytest.raises(ValidationError) as exc_info:
            UserRegister(
                name="Test User",
                email="test@example.com",
                password="NoDigitHere!"
            )
        assert "digit" in str(exc_info.value)

    def test_password_valid(self):
        """Test valid password passes validation"""
        user = UserRegister(
            name="Test User",
            email="test@example.com",
            password="ValidPass123!"
        )
        assert user.password == "ValidPass123!"

class TestEmailValidation:
    def test_invalid_email_format(self):
        """Test invalid email format"""
        with pytest.raises(ValidationError):
            UserRegister(
                name="Test User",
                email="not-an-email",
                password="ValidPass123!"
            )

    def test_valid_email_format(self):
        """Test valid email format"""
        user = UserRegister(
            name="Test User",
            email="valid@example.com",
            password="ValidPass123!"
        )
        assert user.email == "valid@example.com"

class TestNameValidation:
    def test_empty_name(self, client):
        """Test registration with empty name - Pydantic validation should catch this"""
        # Pydantic validation catches empty name
        response = client.post("/api/v1/users/register", json={
            "name": "",
            "email": "test@example.com",
            "password": "ValidPass123!"
        })
        # Pydantic validation returns 422
        assert response.status_code == 422

    def test_name_too_long(self, client):
        """Test registration with name too long - Pydantic validation should catch this"""
        long_name = "a" * 101
        response = client.post("/api/v1/users/register", json={
            "name": long_name,
            "email": "test@example.com",
            "password": "ValidPass123!"
        })
        # Pydantic validation returns 422
        assert response.status_code == 422