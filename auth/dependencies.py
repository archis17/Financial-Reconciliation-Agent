"""
FastAPI dependencies for authentication.
"""

from typing import Optional, Union
from uuid import UUID
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from database.session import get_db, IS_SQLITE
from database.models import User
from database.repository import UserRepository
from .service import decode_token

# HTTP Bearer token scheme
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Get current authenticated user from JWT token.
    
    Args:
        credentials: HTTP Bearer token credentials
        db: Database session
    
    Returns:
        User: Authenticated user
    
    Raises:
        HTTPException: If token is invalid or user not found
    """
    token = credentials.credentials
    token_data = decode_token(token)
    
    user_repo = UserRepository(db)
    # Handle both UUID (PostgreSQL) and string (SQLite) user IDs
    user_id: Union[UUID, str] = token_data.user_id if IS_SQLITE else UUID(token_data.user_id)
    user = await user_repo.get_by_id(user_id)
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    
    return user


async def require_auth(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Dependency that requires authentication.
    Simply returns the current user if authenticated.
    
    Args:
        current_user: Current authenticated user
    
    Returns:
        User: Authenticated user
    """
    return current_user


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
    db: AsyncSession = Depends(get_db)
) -> Optional[User]:
    """
    Get current user if authenticated, otherwise return None.
    Useful for endpoints that work with or without authentication.
    
    Args:
        credentials: Optional HTTP Bearer token credentials
        db: Database session
    
    Returns:
        Optional[User]: User if authenticated, None otherwise
    """
    if credentials is None:
        return None
    
    try:
        token = credentials.credentials
        token_data = decode_token(token)
        
        user_repo = UserRepository(db)
        # Handle both UUID (PostgreSQL) and string (SQLite) user IDs
        user_id: Union[UUID, str] = token_data.user_id if IS_SQLITE else UUID(token_data.user_id)
        user = await user_repo.get_by_id(user_id)
        
        if user is None or not user.is_active:
            return None
        
        return user
    except Exception:
        return None

