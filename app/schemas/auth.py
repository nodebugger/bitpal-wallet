from pydantic import BaseModel


class GoogleAuthRequest(BaseModel):
    """Schema for Google authentication request."""
    token: str


class TokenResponse(BaseModel):
    """Schema for JWT token response."""
    access_token: str
    token_type: str = "bearer"
    user: dict
