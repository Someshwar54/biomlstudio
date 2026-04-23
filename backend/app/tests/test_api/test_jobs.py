"""
Tests for job endpoints
"""

import pytest
from fastapi.testclient import TestClient


class TestJobEndpoints:
    """Test ML job management endpoints"""
    
    def test_create_job_success(self, authenticated_client: TestClient, test_dataset, test_job_config, mock_celery_task):
        """Test successful job creation"""
        job_data = {
            "name": "Test Training Job",
            "description": "Test job description",
            "job_type": "training",
            "config": test_job_config,
            "dataset_id": test_dataset.id
        }
        
        response = authenticated_client.post("/api/v1/jobs/", json=job_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == job_data["name"]
        assert data["job_type"] == job_data["job_type"]
        assert data["status"] == "queued"
        assert "id" in data
    
    def test_create_job_invalid_config(self, authenticated_client: TestClient, test_dataset):
        """Test job creation with invalid configuration"""
        job_data = {
            "name": "Invalid Job",
            "job_type": "invalid_type",
            "config": {},
            "dataset_id": test_dataset.id
        }
        
        response = authenticated_client.post("/api/v1/jobs/", json=job_data)
        
        assert response.status_code == 422  # Validation error
    
    def test_create_job_nonexistent_dataset(self, authenticated_client: TestClient, test_job_config):
        """Test job creation with non-existent dataset"""
        job_data = {
            "name": "Test Job",
            "job_type": "training",
            "config": test_job_config,
            "dataset_id": 999999
        }
        
        response = authenticated_client.post("/api/v1/jobs/", json=job_data)
        
        assert response.status_code in [400, 404]
    
    def test_list_jobs(self, authenticated_client: TestClient, test_job):
        """Test listing user jobs"""
        response = authenticated_client.get("/api/v1/jobs/")
        
        assert response.status_code == 200
        data = response.json()
        assert "jobs" in data
        assert "total" in data
        assert isinstance(data["jobs"], list)
        assert data["total"] >= 1
    
    def test_list_jobs_with_filters(self, authenticated_client: TestClient, test_job):
        """Test listing jobs with filters"""
        response = authenticated_client.get("/api/v1/jobs/?job_type=training&status=pending")
        
        assert response.status_code == 200
        data = response.json()
        assert "jobs" in data
    
    def test_get_job_by_id(self, authenticated_client: TestClient, test_job):
        """Test getting specific job"""
        response = authenticated_client.get(f"/api/v1/jobs/{test_job.id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_job.id
        assert data["name"] == test_job.name
    
    def test_get_job_not_found(self, authenticated_client: TestClient):
        """Test getting non-existent job"""
        response = authenticated_client.get("/api/v1/jobs/999999")
        
        assert response.status_code == 404
    
    def test_update_job(self, authenticated_client: TestClient, test_job):
        """Test updating job information"""
        update_data = {
            "name": "Updated Job Name",
            "description": "Updated description"
        }
        
        response = authenticated_client.put(f"/api/v1/jobs/{test_job.id}", json=update_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == update_data["name"]
    
    def test_cancel_job(self, authenticated_client: TestClient, test_job):
        """Test cancelling a job"""
        response = authenticated_client.post(f"/api/v1/jobs/{test_job.id}/cancel")
        
        assert response.status_code == 200
        data = response.json()
        assert "cancelled successfully" in data["message"].lower()
    
    def test_get_job_metrics(self, authenticated_client: TestClient, test_job):
        """Test getting job metrics"""
        # Set some metrics on the job
        test_job.metrics = {"accuracy": 0.95, "precision": 0.94}
        
        response = authenticated_client.get(f"/api/v1/jobs/{test_job.id}/metrics")
        
        assert response.status_code == 200
        data = response.json()
        assert "metrics" in data
    
    def test_get_job_logs(self, authenticated_client: TestClient, test_job):
        """Test getting job logs"""
        response = authenticated_client.get(f"/api/v1/jobs/{test_job.id}/logs")
        
        assert response.status_code == 200
        data = response.json()
        assert "logs" in data
        assert "job_id" in data
    
    def test_delete_job(self, authenticated_client: TestClient, test_job):
        """Test deleting a job"""
        response = authenticated_client.delete(f"/api/v1/jobs/{test_job.id}")
        
        assert response.status_code == 200
        data = response.json()
        assert "deleted successfully" in data["message"].lower()
