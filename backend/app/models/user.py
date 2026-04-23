"""
User model for authentication and user management
"""

from datetime import datetime, timedelta
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Column, DateTime, String, Text, Integer
from sqlalchemy.orm import relationship

from .base import Base

if TYPE_CHECKING:
    from .dataset import Dataset
    from .job import Job
    from .ml_model import MLModel


class User(Base):
    """User model for authentication and profile management"""
    
    __tablename__ = "users"
    
    # Basic user information
    email = Column(String(255), unique=True, index=True, nullable=False)
    full_name = Column(String(255), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    
    # User status
    is_active = Column(Boolean, default=True, nullable=False)
    is_admin = Column(Boolean, default=False, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    
    # Profile information
    bio = Column(Text)
    institution = Column(String(255))
    research_interests = Column(Text)
    
    # Authentication tracking
    last_login = Column(DateTime)
    login_count = Column(Integer, default=0)
    failed_login_attempts = Column(Integer, default=0)
    account_locked_until = Column(DateTime)
    
    # API access
    api_key = Column(String(255), unique=True, index=True)
    api_key_created_at = Column(DateTime)
    
    # Email verification
    verification_token = Column(String(255))
    verification_token_expires = Column(DateTime)
    
    # Password reset
    reset_token = Column(String(255))
    reset_token_expires = Column(DateTime)
    
    # Relationships
    datasets = relationship(
        "Dataset", 
        back_populates="owner", 
        cascade="all, delete-orphan",
        lazy="dynamic"
    )
    
    jobs = relationship(
        "Job", 
        back_populates="user", 
        cascade="all, delete-orphan",
        lazy="dynamic"
    )
    
    models = relationship(
        "MLModel", 
        back_populates="user", 
        cascade="all, delete-orphan",
        lazy="dynamic"
    )
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, email='{self.email}')>"
    
    @property
    def is_locked(self) -> bool:
        """Check if account is locked"""
        if self.account_locked_until:
            return datetime.utcnow() < self.account_locked_until
        return False
    
    def lock_account(self, duration_minutes: int = 30) -> None:
        """Lock account for specified duration"""
        self.account_locked_until = (
            datetime.utcnow() + timedelta(minutes=duration_minutes)
        )
    
    def unlock_account(self) -> None:
        """Unlock account"""
        self.account_locked_until = None
        self.failed_login_attempts = 0
    
    def increment_failed_login(self) -> None:
        """Increment failed login attempts"""
        self.failed_login_attempts += 1
        
        # Lock account after 5 failed attempts
        if self.failed_login_attempts >= 5:
            self.lock_account()
    
    def successful_login(self) -> None:
        """Record successful login"""
        self.last_login = datetime.utcnow()
        self.login_count += 1
        self.failed_login_attempts = 0
        self.account_locked_until = None
