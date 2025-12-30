"""
Authentication service for JWT token management and password hashing.
"""

import os
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status

from database.models import User
from .models import TokenData

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT Configuration
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
JWT_REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("JWT_REFRESH_TOKEN_EXPIRE_DAYS", "7"))


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    """Create JWT refresh token."""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=JWT_REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> TokenData:
    """Decode and validate JWT token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        user_id: str = payload.get("sub")
        email: str = payload.get("email")
        token_type: str = payload.get("type")
        
        if user_id is None or email is None:
            raise credentials_exception
        
        if token_type != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type"
            )
        
        return TokenData(user_id=user_id, email=email)
    except JWTError:
        raise credentials_exception


def decode_refresh_token(token: str) -> TokenData:
    """Decode and validate refresh token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate refresh token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        user_id: str = payload.get("sub")
        email: str = payload.get("email")
        token_type: str = payload.get("type")
        
        if user_id is None or email is None:
            raise credentials_exception
        
        if token_type != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type"
            )
        
        return TokenData(user_id=user_id, email=email)
    except JWTError:
        raise credentials_exception


class AuthService:
    """Authentication service."""
    
    @staticmethod
    def validate_password_strength(password: str) -> bool:
        """Validate password strength."""
        if len(password) < 8:
            return False
        # Add more validation rules as needed
        return True
    
    @staticmethod
    def create_tokens(user: User) -> dict:
        """Create access and refresh tokens for a user."""
        data = {
            "sub": str(user.id),
            "email": user.email,
        }
        access_token = create_access_token(data)
        refresh_token = create_refresh_token(data)
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }

