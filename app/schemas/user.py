"""User schemas for request/response validation."""
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field
from typing import Optional


class UserBase(BaseModel):
    """Base user schema."""
    email: EmailStr
    username: str


class UserCreate(UserBase):
    """Schema for creating a user."""
    google_id: str


class UserResponse(UserBase):
    """Schema for user response."""
    id: str
    google_id: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class UserWithWallet(UserResponse):
    """Schema for user response with wallet info."""
    wallet_number: Optional[str] = None
    balance: Optional[float] = None
