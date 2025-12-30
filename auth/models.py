"""
Pydantic models for authentication.
"""

from typing import Optional
from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    """User registration model."""
    email: EmailStr
    password: str = Field(..., min_length=8, description="Password must be at least 8 characters")


class UserResponse(BaseModel):
    """User response model."""
    id: str
    email: str
    is_active: bool
    created_at: str
    
    class Config:
        from_attributes = True


class Token(BaseModel):
    """Token response model."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Token data model."""
    user_id: Optional[str] = None
    email: Optional[str] = None

