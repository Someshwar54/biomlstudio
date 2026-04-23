"""
Dependency injection for FastAPI routes
"""
#Auth: JWT

import logging
from typing import Generator, Optional

from fastapi import Depends, HTTPException, status, Query
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import SessionLocal
from app.models.user import User
from app.schemas.auth import TokenData

logger = logging.getLogger(__name__)

# Security scheme
security = HTTPBearer()


def get_db() -> Generator[Session, None, None]:
    """
    Database dependency that provides a SQLAlchemy session.
    Automatically handles session cleanup.
    """
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Database session error: {e}")
        db.rollback()
        raise
    finally:
        db.close()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Get current authenticated user from JWT token.
    
    Args:
        credentials: JWT token from HTTP Authorization header
        db: Database session
        
    Returns:
        User: Authenticated user object
        
    Raises:
        HTTPException: If token is invalid or user not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        token = credentials.credentials
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        
        user_id: int = payload.get("sub")
        if user_id is None:
            logger.warning("Token missing user ID")
            raise credentials_exception
            
        token_data = TokenData(user_id=user_id)
        
    except JWTError as e:
        logger.warning(f"JWT decode error: {e}")
        raise credentials_exception
    
    # Get user from database
    user = db.query(User).filter(User.id == token_data.user_id).first()
    if user is None:
        logger.warning(f"User not found: {token_data.user_id}")
        raise credentials_exception
    
    if not user.is_active:
        logger.warning(f"Inactive user attempted access: {user.id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Get current active user (additional check for user status).
    
    Args:
        current_user: User from get_current_user dependency
        
    Returns:
        User: Active user object
        
    Raises:
        HTTPException: If user is inactive
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    return current_user


async def get_user_from_token_query(
    token: Optional[str] = Query(None),
    db: Session = Depends(get_db)
) -> User:
    """
    Get current user from JWT token in query parameter (for file downloads).
    
    Args:
        token: JWT token from query parameter
        db: Database session
        
    Returns:
        User: Authenticated user object
        
    Raises:
        HTTPException: If token is invalid or user not found
    """
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token required",
        )
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
    )
    
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        
        user_id: int = payload.get("sub")
        if user_id is None:
            raise credentials_exception
            
    except JWTError as e:
        logger.warning(f"JWT decode error from query token: {e}")
        raise credentials_exception
    
    # Get user from database
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    
    return user


def require_admin(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """
    Require admin privileges for endpoint access.
    
    Args:
        current_user: Current active user
        
    Returns:
        User: Admin user object
        
    Raises:
        HTTPException: If user is not admin
    """
    if not current_user.is_admin:
        logger.warning(f"Non-admin user attempted admin access: {current_user.id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient privileges"
        )
    return current_user


class CommonQueryParams:
    """Common query parameters for list endpoints"""
    
    def __init__(
        self,
        skip: int = 0,
        limit: int = 100,
        sort_by: str = "created_at",
        sort_order: str = "desc"
    ):
        self.skip = skip
        self.limit = min(limit, 1000)  # Max 1000 items per page
        self.sort_by = sort_by
        self.sort_order = sort_order.lower()


async def validate_file_upload(
    file_size: int,
    file_extension: str
) -> bool:
    """
    Validate file upload parameters.
    
    Args:
        file_size: Size of uploaded file in bytes
        file_extension: File extension
        
    Returns:
        bool: True if valid
        
    Raises:
        HTTPException: If file is invalid
    """
    # Check file size
    max_size_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if file_size > max_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Maximum size: {settings.MAX_UPLOAD_SIZE_MB}MB"
        )
    
    # Check file extension
    if file_extension.lower() not in settings.ALLOWED_FILE_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported file type. Allowed: {', '.join(settings.ALLOWED_FILE_EXTENSIONS)}"
        )
    
    return True


# Rate limiting dependency (simplified)
class RateLimiter:
    """Simple rate limiter for API endpoints"""
    
    def __init__(self, calls: int = 100, period: int = 60):
        self.calls = calls
        self.period = period
        self.call_log = {}
    
    async def __call__(self, request) -> bool:
        # Implementation would track requests per IP/user
        # For now, just return True (no limiting)
        return True


# Create rate limiter instances
rate_limiter = RateLimiter(calls=settings.RATE_LIMIT_PER_MINUTE, period=60)
