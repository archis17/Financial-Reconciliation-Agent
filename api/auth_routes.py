"""
Authentication API endpoints.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Form
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from database.session import get_db
from database.repository import UserRepository, AuditLogRepository
from auth.models import UserCreate, UserResponse, Token
from auth.service import (
    AuthService,
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
)
from auth.dependencies import get_current_user, security
from database.models import User
from api.metrics import user_logins_total

router = APIRouter(prefix="/api/auth", tags=["authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Register a new user.
    
    Args:
        user_data: User registration data
        db: Database session
    
    Returns:
        UserResponse: Created user
    
    Raises:
        HTTPException: If email already exists or password is weak
    """
    # Validate password strength
    if not AuthService.validate_password_strength(user_data.password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters long"
        )
    
    # Check if user already exists
    user_repo = UserRepository(db)
    existing_user = await user_repo.get_by_email(user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create user
    hashed_password = get_password_hash(user_data.password)
    user = await user_repo.create(
        email=user_data.email,
        hashed_password=hashed_password
    )
    
    # Log registration
    audit_repo = AuditLogRepository(db)
    await audit_repo.create(
        action="user_registered",
        user_id=user.id,
        resource_type="user",
        resource_id=str(user.id)
    )
    
    await db.commit()
    
    return UserResponse(
        id=str(user.id),
        email=user.email,
        is_active=user.is_active,
        created_at=user.created_at.isoformat()
    )


@router.post("/login", response_model=Token)
async def login(
    email: str = Form(...),
    password: str = Form(...),
    db: AsyncSession = Depends(get_db)
):
    """
    Login and get access token.
    
    Args:
        email: User email
        password: User password
        db: Database session
    
    Returns:
        Token: Access and refresh tokens
    
    Raises:
        HTTPException: If credentials are invalid
    """
    user_repo = UserRepository(db)
    user = await user_repo.get_by_email(email)
    
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )
    
    # Create tokens
    tokens = AuthService.create_tokens(user)
    
    # Record metrics
    user_logins_total.inc()
    
    # Log login
    audit_repo = AuditLogRepository(db)
    await audit_repo.create(
        action="user_login",
        user_id=user.id,
        resource_type="user",
        resource_id=str(user.id)
    )
    
    await db.commit()
    
    return Token(**tokens)


@router.post("/refresh", response_model=Token)
async def refresh_token(
    refresh_token: str = Form(...),
    db: AsyncSession = Depends(get_db)
):
    """
    Refresh access token using refresh token.
    
    Args:
        refresh_token: Refresh token
        db: Database session
    
    Returns:
        Token: New access and refresh tokens
    
    Raises:
        HTTPException: If refresh token is invalid
    """
    try:
        token_data = decode_refresh_token(refresh_token)
        
        user_repo = UserRepository(db)
        # Handle both UUID (PostgreSQL) and string (SQLite) user IDs
        from database.session import IS_SQLITE
        from typing import Union
        from uuid import UUID
        user_id: Union[UUID, str] = token_data.user_id if IS_SQLITE else UUID(token_data.user_id)
        user = await user_repo.get_by_id(user_id)
        
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        # Create new tokens
        tokens = AuthService.create_tokens(user)
        
        return Token(**tokens)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """
    Get current user information.
    
    Args:
        current_user: Current authenticated user
    
    Returns:
        UserResponse: Current user information
    """
    return UserResponse(
        id=str(current_user.id),
        email=current_user.email,
        is_active=current_user.is_active,
        created_at=current_user.created_at.isoformat()
    )

