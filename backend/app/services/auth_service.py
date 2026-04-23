"""
Authentication service for user management and security
"""

import logging
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db_context
from app.core.security import (
    create_access_token, create_refresh_token, get_password_hash,
    verify_password, generate_api_key
)
from app.models.user import User
from app.schemas.auth import UserCreate

logger = logging.getLogger(__name__)


class AuthService:
    """Service for authentication and user management"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    async def create_user(self, user_data: UserCreate) -> User:
        """
        Create a new user account.
        
        Args:
            user_data: User creation data
            
        Returns:
            User: Created user instance
            
        Raises:
            ValueError: If email already exists
        """
        with get_db_context() as db:
            # Check if user already exists
            existing_user = db.query(User).filter(
                User.email == user_data.email
            ).first()
            
            if existing_user:
                raise ValueError("Email already registered")
            
            # Create new user
            hashed_password = get_password_hash(user_data.password)
            
            db_user = User(
                email=user_data.email,
                full_name=user_data.full_name,
                hashed_password=hashed_password,
                is_active=True,
                is_verified=False,  # Require email verification
                created_at=datetime.utcnow()
            )
            
            db.add(db_user)
            db.commit()
            db.refresh(db_user)
            
            self.logger.info(f"User created: {db_user.email}")
            return db_user
    
    async def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """
        Authenticate user credentials.
        
        Args:
            email: User email
            password: User password
            
        Returns:
            User: Authenticated user or None
        """
        with get_db_context() as db:
            user = db.query(User).filter(User.email == email).first()
            
            if not user:
                self.logger.warning(f"Authentication failed - user not found: {email}")
                return None
            
            # Check if account is locked
            if user.is_locked:
                self.logger.warning(f"Authentication failed - account locked: {email}")
                return None
            
            # Check if account is active
            if not user.is_active:
                self.logger.warning(f"Authentication failed - account inactive: {email}")
                return None
            
            # Verify password
            if not verify_password(password, user.hashed_password):
                user.increment_failed_login()
                db.commit()
                self.logger.warning(f"Authentication failed - wrong password: {email}")
                return None
            
            # Successful login
            user.successful_login()
            db.commit()
            
            self.logger.info(f"User authenticated: {email}")
            return user
    
    async def create_access_token_for_user(self, user: User) -> str:
        """
        Create access token for user.
        
        Args:
            user: User instance
            
        Returns:
            str: JWT access token
        """
        token_data = {"sub": str(user.id), "email": user.email}
        access_token = create_access_token(token_data)
        
        return access_token
    
    async def create_refresh_token_for_user(self, user: User) -> str:
        """
        Create refresh token for user.
        
        Args:
            user: User instance
            
        Returns:
            str: JWT refresh token
        """
        token_data = {"sub": str(user.id), "email": user.email}
        refresh_token = create_refresh_token(token_data)
        
        return refresh_token
    
    async def change_password(
        self, 
        user_id: int, 
        current_password: str, 
        new_password: str
    ) -> bool:
        """
        Change user password.
        
        Args:
            user_id: User ID
            current_password: Current password
            new_password: New password
            
        Returns:
            bool: True if password changed successfully
            
        Raises:
            ValueError: If current password is incorrect
        """
        with get_db_context() as db:
            user = db.query(User).filter(User.id == user_id).first()
            
            if not user:
                raise ValueError("User not found")
            
            # Verify current password
            if not verify_password(current_password, user.hashed_password):
                raise ValueError("Current password is incorrect")
            
            # Update password
            user.hashed_password = get_password_hash(new_password)
            user.updated_at = datetime.utcnow()
            db.commit()
            
            self.logger.info(f"Password changed for user: {user.email}")
            return True
    
    async def generate_api_key_for_user(self, user_id: int) -> str:
        """
        Generate API key for user.
        
        Args:
            user_id: User ID
            
        Returns:
            str: Generated API key
        """
        with get_db_context() as db:
            user = db.query(User).filter(User.id == user_id).first()
            
            if not user:
                raise ValueError("User not found")
            
            api_key = generate_api_key()
            user.api_key = api_key
            user.api_key_created_at = datetime.utcnow()
            user.updated_at = datetime.utcnow()
            
            db.commit()
            
            self.logger.info(f"API key generated for user: {user.email}")
            return api_key
    
    async def verify_api_key(self, api_key: str) -> Optional[User]:
        """
        Verify API key and return associated user.
        
        Args:
            api_key: API key to verify
            
        Returns:
            User: User associated with API key or None
        """
        with get_db_context() as db:
            user = db.query(User).filter(
                User.api_key == api_key,
                User.is_active == True
            ).first()
            
            if user:
                user.last_login = datetime.utcnow()
                db.commit()
            
            return user
    
    async def deactivate_user(self, user_id: int) -> bool:
        """
        Deactivate user account.
        
        Args:
            user_id: User ID to deactivate
            
        Returns:
            bool: True if deactivated successfully
        """
        with get_db_context() as db:
            user = db.query(User).filter(User.id == user_id).first()
            
            if not user:
                return False
            
            user.is_active = False
            user.updated_at = datetime.utcnow()
            db.commit()
            
            self.logger.info(f"User deactivated: {user.email}")
            return True
    
    async def reactivate_user(self, user_id: int) -> bool:
        """
        Reactivate user account.
        
        Args:
            user_id: User ID to reactivate
            
        Returns:
            bool: True if reactivated successfully
        """
        with get_db_context() as db:
            user = db.query(User).filter(User.id == user_id).first()
            
            if not user:
                return False
            
            user.is_active = True
            user.unlock_account()  # Clear any account locks
            user.updated_at = datetime.utcnow()
            db.commit()
            
            self.logger.info(f"User reactivated: {user.email}")
            return True
