"""Authentication dependencies for JWT and API Key authentication."""
from typing import Optional, List
from fastapi import Depends, HTTPException, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from jose import JWTError

from app.db.session import get_db
from app.models.user import User
from app.models.api_key import APIKey
from app.core.security import verify_token
from app.services.api_key_service import APIKeyService


# HTTP Bearer scheme for JWT
bearer_scheme = HTTPBearer(auto_error=False)


class AuthenticatedUser:
    """Container for authenticated user info."""
    
    def __init__(
        self, 
        user: User, 
        auth_type: str,  # "jwt" or "api_key"
        api_key: Optional[APIKey] = None
    ):
        self.user = user
        self.auth_type = auth_type
        self.api_key = api_key
        self.permissions = api_key.permissions if api_key else ["deposit", "transfer", "read"]
    
    def has_permission(self, permission: str) -> bool:
        """Check if user has a specific permission."""
        return permission in self.permissions


async def get_user_from_jwt(
    token: str,
    db: AsyncSession
) -> Optional[User]:
    """Get user from JWT token."""
    try:
        payload = verify_token(token)
        user_id = payload.get("sub")
        if not user_id:
            return None
        
        stmt = select(User).where(User.id == user_id)
        result = await db.execute(stmt)
        return result.scalars().first()
    except JWTError:
        return None


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    x_api_key: Optional[str] = Header(None, alias="x-api-key"),
    db: AsyncSession = Depends(get_db)
) -> AuthenticatedUser:
    """
    Get current authenticated user from JWT or API key.
    
    Priority:
    1. JWT token in Authorization header
    2. API key in x-api-key header
    
    Returns:
        AuthenticatedUser: Authenticated user container
        
    Raises:
        HTTPException: If authentication fails
    """
    # Try JWT authentication first
    if credentials and credentials.credentials:
        user = await get_user_from_jwt(credentials.credentials, db)
        if user:
            return AuthenticatedUser(user=user, auth_type="jwt")
    
    # Try API key authentication
    if x_api_key:
        result = await APIKeyService.verify_api_key(x_api_key, db)
        if result:
            api_key, user = result
            return AuthenticatedUser(user=user, auth_type="api_key", api_key=api_key)
        else:
            raise HTTPException(
                status_code=401,
                detail={
                    "status_code": 401,
                    "status": "error",
                    "message": "Invalid or expired API key",
                    "data": None
                }
            )
    
    # No valid authentication found
    raise HTTPException(
        status_code=401,
        detail={
            "status_code": 401,
            "status": "error",
            "message": "Authentication required. Provide JWT token or API key.",
            "data": None
        }
    )


async def get_current_user_jwt_only(
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer()),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Get current user from JWT only (for endpoints that don't support API keys).
    
    Returns:
        User: Authenticated user
        
    Raises:
        HTTPException: If authentication fails
    """
    user = await get_user_from_jwt(credentials.credentials, db)
    if not user:
        raise HTTPException(
            status_code=401,
            detail={
                "status_code": 401,
                "status": "error",
                "message": "Invalid or expired JWT token",
                "data": None
            }
        )
    return user


def require_permission(permission: str):
    """
    Dependency factory for requiring specific permissions.
    
    Args:
        permission: Required permission (deposit, transfer, read)
        
    Returns:
        Dependency function that checks permission
    """
    async def check_permission(
        auth_user: AuthenticatedUser = Depends(get_current_user)
    ) -> AuthenticatedUser:
        if not auth_user.has_permission(permission):
            raise HTTPException(
                status_code=403,
                detail={
                    "status_code": 403,
                    "status": "error",
                    "message": f"API key does not have '{permission}' permission",
                    "data": None
                }
            )
        return auth_user
    
    return check_permission


# Pre-configured permission dependencies
require_deposit_permission = require_permission("deposit")
require_transfer_permission = require_permission("transfer")
require_read_permission = require_permission("read")
