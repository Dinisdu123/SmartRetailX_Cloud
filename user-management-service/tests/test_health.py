import pytest
from fastapi.testclient import TestClient

def test_health_endpoint_success(client):
    """Test health check endpoint returns correct status"""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "user-management-service"
    assert data["database"] == "connected"
    assert "version" in data

def test_root_endpoint(client):
    """Test root endpoint returns service information"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "service" in data
    assert "version" in data
    assert "documentation" in data
    assert "health" in data
    assert "metrics" in data

def test_metrics_endpoint(client):
    """Test metrics endpoint is accessible"""
    response = client.get("/api/v1/metrics")
    assert response.status_code == 200
    # Prometheus metrics should be returned
    assert "# HELP" in response.text or response.text != ""