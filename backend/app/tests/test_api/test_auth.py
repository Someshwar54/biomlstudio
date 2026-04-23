"""
Tests for authentication endpoints
"""

import pytest
from fastapi.testclient import TestClient


class TestAuthenticationEndpoints:
    """Test authentication and user management endpoints"""
    
    def test_user_registration_success(self, client: TestClient, test_user_data):
        """Test successful user registration"""
        response = client.post("/api/v1/auth/register", json=test_user_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == test_user_data["email"]
        assert data["full_name"] == test_user_data["full_name"]
        assert data["is_active"] is True
        assert data["is_admin"] is False
        assert "id" in data
        assert "password" not in data  # Password should not be returned
    
    def test_user_registration_duplicate_email(self, client: TestClient, test_user_data):
        """Test registration with duplicate email"""
        # Register first user
        client.post("/api/v1/auth/register", json=test_user_data)
        
        # Try to register with same email
        response = client.post("/api/v1/auth/register", json=test_user_data)
        
        assert response.status_code == 400
        data = response.json()
        assert "already registered" in data["detail"].lower()
    
    def test_user_registration_invalid_email(self, client: TestClient, test_user_data):
        """Test registration with invalid email"""
        test_user_data["email"] = "invalid-email"
        
        response = client.post("/api/v1/auth/register", json=test_user_data)
        
        assert response.status_code == 422  # Validation error
    
    def test_user_registration_weak_password(self, client: TestClient, test_user_data):
        """Test registration with weak password"""
        test_user_data["password"] = "weak"
        
        response = client.post("/api/v1/auth/register", json=test_user_data)
        
        assert response.status_code == 422  # Validation error
    
    def test_user_login_success(self, client: TestClient, test_user, test_user_data):
        """Test successful user login"""
        login_data = {
            "username": test_user_data["email"],
            "password": test_user_data["password"]
        }
        
        response = client.post("/api/v1/auth/login", data=login_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert "expires_in" in data
    
    def test_user_login_invalid_email(self, client: TestClient):
        """Test login with invalid email"""
        login_data = {
            "username": "nonexistent@example.com",
            "password": "anypassword"
        }
        
        response = client.post("/api/v1/auth/login", data=login_data)
        
        assert response.status_code == 401
        data = response.json()
        assert "incorrect" in data["detail"].lower()
    
    def test_user_login_wrong_password(self, client: TestClient, test_user):
        """Test login with wrong password"""
        login_data = {
            "username": test_user.email,
            "password": "wrongpassword"
        }
        
        response = client.post("/api/v1/auth/login", data=login_data)
        
        assert response.status_code == 401
    
    def test_get_current_user_authenticated(self, authenticated_client: TestClient, test_user):
        """Test getting current user information when authenticated"""
        response = authenticated_client.get("/api/v1/auth/me")
        
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == test_user.email
        assert data["full_name"] == test_user.full_name
        assert data["id"] == test_user.id
    
    def test_get_current_user_unauthenticated(self, client: TestClient):
        """Test getting current user without authentication"""
        response = client.get("/api/v1/auth/me")
        
        assert response.status_code == 401
    
    def test_update_current_user(self, authenticated_client: TestClient, test_user):
        """Test updating current user information"""
        update_data = {
            "full_name": "Updated Test User",
            "bio": "Updated bio"
        }
        
        response = authenticated_client.put("/api/v1/auth/me", json=update_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["full_name"] == update_data["full_name"]
    
    def test_change_password_success(self, authenticated_client: TestClient, test_user_data):
        """Test successful password change"""
        password_data = {
            "current_password": test_user_data["password"],
            "new_password": "NewStrongPassword123!"
        }
        
        response = authenticated_client.post("/api/v1/auth/change-password", json=password_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "successfully" in data["message"].lower()
    
    def test_change_password_wrong_current(self, authenticated_client: TestClient):
        """Test password change with wrong current password"""
        password_data = {
            "current_password": "wrongpassword",
            "new_password": "NewStrongPassword123!"
        }
        
        response = authenticated_client.post("/api/v1/auth/change-password", json=password_data)
        
        assert response.status_code == 400
        data = response.json()
        assert "incorrect" in data["detail"].lower()
    
    def test_logout(self, authenticated_client: TestClient):
        """Test user logout"""
        response = authenticated_client.post("/api/v1/auth/logout")
        
        assert response.status_code == 200
        data = response.json()
        assert "logged out" in data["message"].lower()
