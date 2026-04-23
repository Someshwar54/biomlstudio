"""
Authentication-related Pydantic schemas
"""

from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class Token(BaseModel):
    """Schema for authentication tokens"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class TokenData(BaseModel):
    """Schema for token payload data"""
    user_id: int
    email: Optional[str] = None


class UserLogin(BaseModel):
    """Schema for user login"""
    email: EmailStr
    password: str


class UserCreate(BaseModel):
    """Schema for user registration"""
    email: EmailStr
    full_name: str = Field(..., min_length=1, max_length=255)
    password: str = Field(..., min_length=8, max_length=100)


class UserResponse(BaseModel):
    """Schema for user data in responses"""
    id: int
    email: EmailStr
    full_name: str
    is_active: bool
    is_admin: bool = False
    is_verified: bool = False

    class Config:
        from_attributes = True


class PasswordChange(BaseModel):
    """Schema for password change"""
    current_password: str
    new_password: str = Field(..., min_length=8, max_length=100)


class PasswordReset(BaseModel):
    """Schema for password reset"""
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    """Schema for password reset confirmation"""
    token: str
    new_password: str = Field(..., min_length=8, max_length=100)
