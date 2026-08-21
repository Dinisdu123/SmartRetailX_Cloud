import pytest
from fastapi.testclient import TestClient
import json
from uuid import uuid4
import concurrent.futures

class TestEdgeCases:
    def test_sql_injection_prevention(self, client):
        """Test SQL injection attempts are handled"""
        response = client.post("/api/v1/users/register", json={
            "name": "'; DROP TABLE users; --",
            "email": "sql@example.com",
            "password": "ValidPass123!"
        })
        # Should either succeed (sanitized) or fail validation
        assert response.status_code in [201, 422]

    def test_xss_prevention(self, client):
        """Test XSS attempts in input are handled"""
        response = client.post("/api/v1/users/register", json={
            "name": "<script>alert('xss')</script>",
            "email": "xss@example.com",
            "password": "ValidPass123!"
        })
        assert response.status_code in [201, 422]

    def test_unicode_characters(self, client):
        """Test Unicode characters in input"""
        response = client.post("/api/v1/users/register", json={
            "name": "测试用户 🚀",
            "email": "unicode@example.com",
            "password": "ValidPass123!"
        })
        assert response.status_code in [201, 422]

    def test_long_input_values(self, client):
        """Test very long input values"""
        long_string = "a" * 10000
        response = client.post("/api/v1/users/register", json={
            "name": long_string,
            "email": f"long@{'a'*100}.com",
            "password": "ValidPass123!"
        })
        # Should fail validation due to length constraints
        assert response.status_code == 422

    def test_special_characters_in_email(self, client):
        """Test special characters in email"""
        response = client.post("/api/v1/users/register", json={
            "name": "Special Email",
            "email": "test+special@example.com",  # Valid email with +
            "password": "ValidPass123!"
        })
        assert response.status_code == 201

    @pytest.mark.skip(reason="Concurrent test needs separate database connection handling")
    def test_concurrent_requests(self, client):
        """Test handling of concurrent requests (simplified)"""
        def make_request():
            return client.post("/api/v1/users/register", json={
                "name": "Concurrent User",
                "email": f"concurrent_{uuid4()}@example.com",
                "password": "ValidPass123!"
            })
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_request) for _ in range(5)]
            results = [f.result() for f in futures]
        
        # All should succeed with unique emails
        success_count = sum(1 for r in results if r.status_code == 201)
        assert success_count == 5