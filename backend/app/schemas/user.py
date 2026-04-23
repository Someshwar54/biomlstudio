"""
User-related Pydantic schemas
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class UserBase(BaseModel):
    """Base user schema with common fields"""
    email: EmailStr
    full_name: str = Field(..., min_length=1, max_length=255)
    bio: Optional[str] = Field(None, max_length=1000)
    institution: Optional[str] = Field(None, max_length=255)
    research_interests: Optional[str] = Field(None, max_length=1000)


class UserCreate(UserBase):
    """Schema for user creation"""
    password: str = Field(..., min_length=8, max_length=100)


class UserUpdate(BaseModel):
    """Schema for user updates"""
    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, min_length=1, max_length=255)
    bio: Optional[str] = Field(None, max_length=1000)
    institution: Optional[str] = Field(None, max_length=255)
    research_interests: Optional[str] = Field(None, max_length=1000)


class UserResponse(UserBase):
    """Schema for user responses"""
    id: int
    is_active: bool
    is_admin: bool
    is_verified: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    last_login: Optional[datetime] = None
    login_count: int = 0

    class Config:
        from_attributes = True


class UserProfile(UserResponse):
    """Extended user profile with statistics"""
    dataset_count: int = 0
    model_count: int = 0
    job_count: int = 0
    api_key: Optional[str] = None
    
    class Config:
        protected_namespaces = ()


class UserListResponse(BaseModel):
    """Schema for paginated user list"""
    users: list[UserResponse]
    total: int
    skip: int
    limit: int
