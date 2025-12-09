"""Authentication endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.auth import GoogleAuthRequest, TokenResponse
from app.services.auth_service import AuthService
from app.core.config import settings

router = APIRouter()


@router.post("/google", response_model=dict)
async def google_auth(
    request: GoogleAuthRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Authenticate user with Google OAuth token.
    Creates user and wallet if user doesn't exist.
    Returns JWT token for subsequent requests.
    
    Args:
        request: Google auth request with token
        db: Database session
        
    Returns:
        dict: JWT token and user info
    """
    try:
        # Verify Google token
        google_info = await AuthService.verify_google_token(
            request.token,
            settings.GOOGLE_CLIENT_ID
        )
        
        # Get or create user (with wallet)
        user, created = await AuthService.get_or_create_user(
            google_id=google_info['sub'],
            email=google_info['email'],
            name=google_info.get('name', google_info['email']),
            db=db
        )
        
        # Load wallet relationship
        await db.refresh(user, ['wallet'])
        
        # Generate JWT
        access_token = AuthService.generate_jwt(user.id)
        
        return {
            "status_code": 200,
            "status": "success",
            "message": "Authentication successful" if not created else "User created and authenticated",
            "data": {
                "access_token": access_token,
                "token_type": "bearer",
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "name": user.name,
                    "wallet_number": user.wallet.wallet_number if user.wallet else None
                }
            }
        }
    
    except ValueError as e:
        raise HTTPException(
            status_code=401,
            detail={
                "status_code": 401,
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
                "message": "Authentication failed",
                "data": None
            }
        )
