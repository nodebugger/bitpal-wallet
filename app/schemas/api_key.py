"""API Key schemas for request/response validation."""
from datetime import datetime
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Literal


class APIKeyCreate(BaseModel):
    """Schema for creating an API key."""
    name: str = Field(..., min_length=1, max_length=255, description="Name for the API key")
    permissions: List[Literal["deposit", "transfer", "read"]] = Field(
        ..., 
        min_length=1,
        description="List of permissions: deposit, transfer, read"
    )
    expiry: Literal["1H", "1D", "1M", "1Y"] = Field(
        ..., 
        description="Expiry duration: 1H (hour), 1D (day), 1M (month), 1Y (year)"
    )
    
    @field_validator('permissions')
    @classmethod
    def validate_permissions(cls, v):
        valid_permissions = {"deposit", "transfer", "read"}
        for perm in v:
            if perm not in valid_permissions:
                raise ValueError(f"Invalid permission: {perm}. Must be one of: {valid_permissions}")
        # Remove duplicates while preserving order
        return list(dict.fromkeys(v))


class APIKeyResponse(BaseModel):
    """Schema for API key creation response."""
    api_key: str = Field(..., description="The generated API key (only shown once)")
    expires_at: datetime = Field(..., description="Expiration datetime")


class APIKeyInfo(BaseModel):
    """Schema for API key information (without the actual key)."""
    id: str
    name: str
    key_prefix: str
    permissions: List[str]
    expires_at: datetime
    is_active: bool
    is_revoked: bool
    created_at: datetime
    last_used_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class APIKeyRollover(BaseModel):
    """Schema for rolling over an expired API key."""
    expired_key_id: str = Field(..., description="ID of the expired API key to rollover")
    expiry: Literal["1H", "1D", "1M", "1Y"] = Field(
        ..., 
        description="New expiry duration: 1H (hour), 1D (day), 1M (month), 1Y (year)"
    )


class APIKeyList(BaseModel):
    """Schema for listing API keys."""
    keys: List[APIKeyInfo]
    total: int
    active_count: int
