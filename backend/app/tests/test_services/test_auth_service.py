"""
Tests for authentication service
"""

import pytest
from app.services.auth_service import AuthService
from app.schemas.auth import UserCreate


class TestAuthService:
    """Test authentication service functionality"""
    
    @pytest.mark.asyncio
    async def test_create_user_success(self, auth_service: AuthService, test_user_data):
        """Test successful user creation"""
        user_create = UserCreate(**test_user_data)
        user = await auth_service.create_user(user_create)
        
        assert user.email == test_user_data["email"]
        assert user.full_name == test_user_data["full_name"]
        assert user.is_active is True
        assert user.is_admin is False
        assert user.hashed_password != test_user_data["password"]  # Should be hashed
        assert len(user.hashed_password) > 0
    
    @pytest.mark.asyncio
    async def test_create_duplicate_user(self, auth_service: AuthService, test_user_data, test_user):
        """Test creating user with duplicate email"""
        user_create = UserCreate(**test_user_data)
        
        with pytest.raises(ValueError, match="already registered"):
            await auth_service.create_user(user_create)
    
    @pytest.mark.asyncio
    async def test_authenticate_user_success(self, auth_service: AuthService, test_user, test_user_data):
        """Test successful user authentication"""
        user = await auth_service.authenticate_user(
            test_user_data["email"],
            test_user_data["password"]
        )
        
        assert user is not None
        assert user.email == test_user_data["email"]
        assert user.id == test_user.id
    
    @pytest.mark.asyncio
    async def test_authenticate_user_invalid_password(self, auth_service: AuthService, test_user, test_user_data):
        """Test authentication with invalid password"""
        user = await auth_service.authenticate_user(
            test_user_data["email"],
            "wrongpassword"
        )
        
        assert user is None
    
    @pytest.mark.asyncio
    async def test_authenticate_nonexistent_user(self, auth_service: AuthService):
        """Test authentication with non-existent user"""
        user = await auth_service.authenticate_user(
            "nonexistent@example.com",
            "anypassword"
        )
        
        assert user is None
    
    @pytest.mark.asyncio
    async def test_create_access_token(self, auth_service: AuthService, test_user):
        """Test access token creation"""
        token = await auth_service.create_access_token_for_user(test_user)
        
        assert isinstance(token, str)
        assert len(token) > 0
        assert "." in token  # JWT tokens contain dots
    
    @pytest.mark.asyncio
    async def test_create_refresh_token(self, auth_service: AuthService, test_user):
        """Test refresh token creation"""
        token = await auth_service.create_refresh_token_for_user(test_user)
        
        assert isinstance(token, str)
        assert len(token) > 0
    
    @pytest.mark.asyncio
    async def test_change_password_success(self, auth_service: AuthService, test_user, test_user_data):
        """Test successful password change"""
        new_password = "NewStrongPassword456!"
        
        success = await auth_service.change_password(
            test_user.id,
            test_user_data["password"],
            new_password
        )
        
        assert success is True
    
    @pytest.mark.asyncio
    async def test_change_password_wrong_current(self, auth_service: AuthService, test_user):
        """Test password change with wrong current password"""
        with pytest.raises(ValueError, match="incorrect"):
            await auth_service.change_password(
                test_user.id,
                "wrongcurrent",
                "NewPassword123!"
            )
    
    @pytest.mark.asyncio
    async def test_generate_api_key(self, auth_service: AuthService, test_user):
        """Test API key generation"""
        api_key = await auth_service.generate_api_key_for_user(test_user.id)
        
        assert isinstance(api_key, str)
        assert api_key.startswith("bml_")
        assert len(api_key) > 20
    
    @pytest.mark.asyncio
    async def test_verify_api_key(self, auth_service: AuthService, test_user):
        """Test API key verification"""
        # Generate API key first
        api_key = await auth_service.generate_api_key_for_user(test_user.id)
        
        # Verify the key
        verified_user = await auth_service.verify_api_key(api_key)
        
        assert verified_user is not None
        assert verified_user.id == test_user.id
    
    @pytest.mark.asyncio
    async def test_verify_invalid_api_key(self, auth_service: AuthService):
        """Test verification of invalid API key"""
        verified_user = await auth_service.verify_api_key("invalid_key")
        
        assert verified_user is None
    
    @pytest.mark.asyncio
    async def test_deactivate_user(self, auth_service: AuthService, test_user):
        """Test user deactivation"""
        success = await auth_service.deactivate_user(test_user.id)
        
        assert success is True
    
    @pytest.mark.asyncio
    async def test_reactivate_user(self, auth_service: AuthService, test_user):
        """Test user reactivation"""
        # Deactivate first
        await auth_service.deactivate_user(test_user.id)
        
        # Then reactivate
        success = await auth_service.reactivate_user(test_user.id)
        
        assert success is True
