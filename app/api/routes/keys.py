"""API Key management endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from app.db.session import get_db
from app.models.user import User
from app.schemas.api_key import APIKeyCreate, APIKeyResponse, APIKeyRollover, APIKeyList, APIKeyInfo
from app.services.api_key_service import APIKeyService
from app.core.dependencies import get_current_user_jwt_only

router = APIRouter()


@router.post("/create", response_model=None)
async def create_api_key(
    request: APIKeyCreate,
    user: User = Depends(get_current_user_jwt_only),
    db: AsyncSession = Depends(get_db)
):
    """
    **Create a new API key**
    
    Generates a new API key with specified permissions and expiry.
    
    **Authentication:** JWT only (API keys cannot create other API keys)
    
    **Request Body:**
    ```json
    {
        "name": "wallet-service",
        "permissions": ["deposit", "transfer", "read"],
        "expiry": "1D"
    }
    ```
    
    **Expiry Options:**
    - `1H` - 1 Hour
    - `1D` - 1 Day
    - `1M` - 1 Month (30 days)
    - `1Y` - 1 Year (365 days)
    
    **Valid Permissions:**
    - `deposit` - Can make deposits
    - `transfer` - Can make transfers
    - `read` - Can read balance and transactions
    
    **Rules:**
    - Maximum 5 active API keys per user
    - The API key is only shown once - store it securely!
    
    **Response:**
    ```json
    {
        "status_code": 201,
        "status": "success",
        "message": "API key created successfully",
        "data": {
            "api_key": "sk_live_xxxxx",
            "expires_at": "2025-01-01T12:00:00Z"
        }
    }
    ```
    """
    try:
        api_key, full_key = await APIKeyService.create_api_key(
            user_id=user.id,
            name=request.name,
            permissions=request.permissions,
            expiry=request.expiry,
            db=db
        )
        
        return {
            "status_code": 201,
            "status": "success",
            "message": "API key created successfully. Store this key securely - it won't be shown again!",
            "data": {
                "api_key": full_key,
                "expires_at": api_key.expires_at.isoformat()
            }
        }
    
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail={
                "status_code": 400,
                "status": "error",
                "message": str(e),
                "data": None
            }
        )
    except Exception as e:
        # Log the actual error for debugging
        import traceback
        print(f"❌ Create API key error: {str(e)}")
        print(traceback.format_exc())
        
        raise HTTPException(
            status_code=500,
            detail={
                "status_code": 500,
                "status": "error",
                "message": f"Failed to create API key: {str(e)}",
                "data": None
            }
        )


@router.post("/rollover", response_model=None)
async def rollover_api_key(
    request: APIKeyRollover,
    user: User = Depends(get_current_user_jwt_only),
    db: AsyncSession = Depends(get_db)
):
    """
    **Rollover an expired API key**
    
    Creates a new API key using the same permissions as an expired key.
    
    **Authentication:** JWT only
    
    **Request Body:**
    ```json
    {
        "expired_key_id": "FGH2485K6KK79GKG9GKGK",
        "expiry": "1M"
    }
    ```
    
    **Rules:**
    - The expired key must truly be expired
    - The new key reuses the same permissions
    - Maximum 5 active API keys limit still applies
    
    **Response:**
    ```json
    {
        "status_code": 201,
        "status": "success",
        "message": "API key rolled over successfully",
        "data": {
            "api_key": "sk_live_xxxxx",
            "expires_at": "2025-02-01T12:00:00Z"
        }
    }
    ```
    """
    try:
        new_key, full_key = await APIKeyService.rollover_api_key(
            expired_key_id=request.expired_key_id,
            user_id=user.id,
            new_expiry=request.expiry,
            db=db
        )
        
        return {
            "status_code": 201,
            "status": "success",
            "message": "API key rolled over successfully. Store this key securely!",
            "data": {
                "api_key": full_key,
                "expires_at": new_key.expires_at.isoformat()
            }
        }
    
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail={
                "status_code": 400,
                "status": "error",
                "message": str(e),
                "data": None
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "status_code": 500,
                "status": "error",
                "message": "Failed to rollover API key",
                "data": None
            }
        )


@router.get("/list", response_model=None)
async def list_api_keys(
    user: User = Depends(get_current_user_jwt_only),
    db: AsyncSession = Depends(get_db)
):
    """
    **List all API keys**
    
    Returns all API keys for the authenticated user.
    
    **Authentication:** JWT only
    
    **Response:**
    ```json
    {
        "status_code": 200,
        "status": "success",
        "message": "API keys retrieved",
        "data": {
            "keys": [...],
            "total": 3,
            "active_count": 2
        }
    }
    ```
    """
    try:
        keys = await APIKeyService.list_user_api_keys(user.id, db)
        
        # Count active keys (not expired and not revoked)
        now = datetime.utcnow()
        active_count = sum(
            1 for k in keys 
            if k.is_active and not k.is_revoked and k.expires_at > now
        )
        
        return {
            "status_code": 200,
            "status": "success",
            "message": "API keys retrieved",
            "data": {
                "keys": [
                    {
                        "id": k.id,
                        "name": k.name,
                        "key_prefix": k.key_prefix,
                        "permissions": k.permissions,
                        "expires_at": k.expires_at.isoformat(),
                        "is_active": k.is_active,
                        "is_revoked": k.is_revoked,
                        "is_expired": k.is_expired(),
                        "created_at": k.created_at.isoformat(),
                        "last_used_at": k.last_used_at.isoformat() if k.last_used_at else None
                    }
                    for k in keys
                ],
                "total": len(keys),
                "active_count": active_count
            }
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "status_code": 500,
                "status": "error",
                "message": "Failed to retrieve API keys",
                "data": None
            }
        )


@router.delete("/{key_id}", response_model=None)
async def revoke_api_key(
    key_id: str,
    user: User = Depends(get_current_user_jwt_only),
    db: AsyncSession = Depends(get_db)
):
    """
    **Revoke an API key**
    
    Permanently revokes an API key. This action cannot be undone.
    
    **Authentication:** JWT only
    
    **Path Parameters:**
    - `key_id` - The ID of the API key to revoke
    
    **Response:**
    ```json
    {
        "status_code": 200,
        "status": "success",
        "message": "API key revoked successfully",
        "data": null
    }
    ```
    """
    try:
        success = await APIKeyService.revoke_api_key(key_id, user.id, db)
        
        if not success:
            raise HTTPException(
                status_code=404,
                detail={
                    "status_code": 404,
                    "status": "error",
                    "message": "API key not found",
                    "data": None
                }
            )
        
        return {
            "status_code": 200,
            "status": "success",
            "message": "API key revoked successfully",
            "data": None
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "status_code": 500,
                "status": "error",
                "message": "Failed to revoke API key",
                "data": None
            }
        )
