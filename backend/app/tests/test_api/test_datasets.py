"""
Tests for dataset endpoints
"""

import pytest
from fastapi.testclient import TestClient
from pathlib import Path


class TestDatasetEndpoints:
    """Test dataset management endpoints"""
    
    def test_upload_dataset_success(self, authenticated_client: TestClient, temp_fasta_file, test_dataset_data):
        """Test successful dataset upload"""
        with open(temp_fasta_file, 'rb') as f:
            files = {"file": ("test.fasta", f, "text/plain")}
            data = {
                "name": test_dataset_data["name"],
                "description": test_dataset_data["description"],
                "dataset_type": test_dataset_data["dataset_type"],
                "is_public": str(test_dataset_data["is_public"]).lower()
            }
            
            response = authenticated_client.post("/api/v1/datasets/upload", files=files, data=data)
        
        assert response.status_code == 200
        result = response.json()
        assert result["name"] == test_dataset_data["name"]
        assert result["dataset_type"] == test_dataset_data["dataset_type"]
        assert result["filename"] == "test.fasta"
        assert "id" in result
    
    def test_upload_dataset_invalid_file_type(self, authenticated_client: TestClient):
        """Test uploading invalid file type"""
        files = {"file": ("test.exe", b"invalid content", "application/octet-stream")}
        data = {
            "name": "Test Dataset",
            "dataset_type": "dna",
            "is_public": "false"
        }
        
        response = authenticated_client.post("/api/v1/datasets/upload", files=files, data=data)
        
        assert response.status_code == 415  # Unsupported Media Type
    
    def test_upload_dataset_unauthenticated(self, client: TestClient, temp_fasta_file):
        """Test dataset upload without authentication"""
        with open(temp_fasta_file, 'rb') as f:
            files = {"file": ("test.fasta", f, "text/plain")}
            data = {"name": "Test Dataset", "dataset_type": "dna"}
            
            response = client.post("/api/v1/datasets/upload", files=files, data=data)
        
        assert response.status_code == 401
    
    def test_list_datasets_authenticated(self, authenticated_client: TestClient, test_dataset):
        """Test listing datasets when authenticated"""
        response = authenticated_client.get("/api/v1/datasets/")
        
        assert response.status_code == 200
        data = response.json()
        assert "datasets" in data
        assert "total" in data
        assert isinstance(data["datasets"], list)
        assert data["total"] >= 1
    
    def test_list_datasets_with_filters(self, authenticated_client: TestClient, test_dataset):
        """Test listing datasets with filters"""
        response = authenticated_client.get("/api/v1/datasets/?dataset_type=dna&limit=5")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["datasets"]) <= 5
    
    def test_get_dataset_by_id_success(self, authenticated_client: TestClient, test_dataset):
        """Test getting specific dataset"""
        response = authenticated_client.get(f"/api/v1/datasets/{test_dataset.id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_dataset.id
        assert data["name"] == test_dataset.name
    
    def test_get_dataset_by_id_not_found(self, authenticated_client: TestClient):
        """Test getting non-existent dataset"""
        response = authenticated_client.get("/api/v1/datasets/999999")
        
        assert response.status_code == 404
    
    def test_get_dataset_by_id_unauthorized(self, client: TestClient):
        """Test getting dataset without authentication"""
        response = client.get("/api/v1/datasets/1")
        
        assert response.status_code == 401
    
    def test_dataset_preview(self, authenticated_client: TestClient, test_dataset):
        """Test dataset preview functionality"""
        response = authenticated_client.get(f"/api/v1/datasets/{test_dataset.id}/preview?rows=2")
        
        assert response.status_code == 200
        data = response.json()
        assert "preview_data" in data
        assert "total_rows" in data
        assert len(data["preview_data"]) <= 2
    
    def test_dataset_stats(self, authenticated_client: TestClient, test_dataset):
        """Test getting dataset statistics"""
        response = authenticated_client.get(f"/api/v1/datasets/{test_dataset.id}/stats")
        
        assert response.status_code == 200
        data = response.json()
        assert "dataset_id" in data
    
    def test_update_dataset(self, authenticated_client: TestClient, test_dataset):
        """Test updating dataset metadata"""
        update_data = {
            "name": "Updated Dataset Name",
            "description": "Updated description"
        }
        
        response = authenticated_client.put(f"/api/v1/datasets/{test_dataset.id}", json=update_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == update_data["name"]
        assert data["description"] == update_data["description"]
    
    def test_delete_dataset(self, authenticated_client: TestClient, test_dataset):
        """Test deleting dataset"""
        response = authenticated_client.delete(f"/api/v1/datasets/{test_dataset.id}")
        
        assert response.status_code == 200
        data = response.json()
        assert "deleted successfully" in data["message"].lower()
    
    def test_validate_dataset(self, authenticated_client: TestClient, test_dataset, mock_celery_task):
        """Test dataset validation"""
        response = authenticated_client.post(f"/api/v1/datasets/{test_dataset.id}/validate")
        
        assert response.status_code == 200
        data = response.json()
        assert "validation_results" in data
