"""
Tests for health check endpoints
"""

import pytest
from fastapi.testclient import TestClient


class TestHealthEndpoints:
    """Test health check endpoints"""
    
    def test_health_check(self, client: TestClient):
        """Test basic health check endpoint"""
        response = client.get("/api/v1/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "service" in data
        assert "timestamp" in data
        assert data["service"] == "BioMLStudio"
    
    def test_detailed_health_check(self, client: TestClient):
        """Test detailed health check endpoint"""
        response = client.get("/api/v1/health/detailed")
        
        assert response.status_code in [200, 503]  # Can be unhealthy in test env
        data = response.json()
        assert "status" in data
        assert "checks" in data
        assert "database" in data["checks"]
        assert "timestamp" in data
    
    def test_readiness_check(self, client: TestClient):
        """Test Kubernetes readiness probe"""
        response = client.get("/api/v1/ready")
        
        assert response.status_code in [200, 503]
        data = response.json()
        assert "status" in data
        assert "timestamp" in data
    
    def test_liveness_check(self, client: TestClient):
        """Test Kubernetes liveness probe"""
        response = client.get("/api/v1/live")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "alive"
        assert "timestamp" in data
