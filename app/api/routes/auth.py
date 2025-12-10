"""Authentication endpoints."""
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse, JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from urllib.parse import urlencode
import httpx

from app.db.session import get_db
from app.schemas.auth import GoogleAuthRequest, TokenResponse
from app.services.auth_service import AuthService
from app.core.config import settings

router = APIRouter()


@router.get("/google")
async def google_sign_in(redirect: bool = Query(True, description="Return redirect or JSON URL")):
    """
    **Step 1: Trigger Google OAuth sign-in flow**
    
    Redirects user to Google's OAuth consent page or returns the auth URL.
    
    **Usage:**
    - Browser/Frontend: `GET /api/v1/auth/google` → Redirects to Google
    - API/Mobile: `GET /api/v1/auth/google?redirect=false` → Returns JSON with URL
    
    **Query Parameters:**
    - redirect (bool): If true (default), returns 302 redirect. If false, returns JSON.
    
    **Response (redirect=true):**
    - 302 Redirect to Google OAuth consent page
    
    **Response (redirect=false):**
    ```json
    {
        "status_code": 200,
        "status": "success",
        "message": "Google OAuth URL generated",
        "data": {
            "google_auth_url": "https://accounts.google.com/o/oauth2/v2/auth?..."
        }
    }
    ```
    
    **Errors:**
    - 400: Invalid redirect URI configuration
    - 500: Internal server error
    """
    try:
        # Validate configuration
        if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_REDIRECT_URI:
            raise HTTPException(
                status_code=400,
                detail={
                    "status_code": 400,
                    "status": "error",
                    "message": "Google OAuth not configured properly",
                    "data": None
                }
            )
        
        # Build Google OAuth URL
        params = {
            "client_id": settings.GOOGLE_CLIENT_ID,
            "redirect_uri": settings.GOOGLE_REDIRECT_URI,
            "response_type": "code",
            "scope": "openid email profile",
            "access_type": "offline",
            "prompt": "consent"
        }
        
        google_auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"
        
        # Return redirect or JSON based on query parameter
        if redirect:
            return RedirectResponse(url=google_auth_url, status_code=302)
        else:
            return {
                "status_code": 200,
                "status": "success",
                "message": "Google OAuth URL generated",
                "data": {
                    "google_auth_url": google_auth_url
                }
            }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "status_code": 500,
                "status": "error",
                "message": "Failed to generate Google OAuth URL",
                "data": None
            }
        )


@router.get("/google/callback")
async def google_callback(
    code: str = Query(..., description="Authorization code from Google"),
    db: AsyncSession = Depends(get_db)
):
    """
    **Step 2: Google OAuth callback endpoint**
    
    Receives the authorization code from Google after user consent.
    Exchanges code for access token, fetches user info, and creates/updates user.
    
    **This endpoint is called by Google, not by your frontend directly.**
    
    **Query Parameters:**
    - code (required): Authorization code from Google
    
    **Success Response:**
    ```json
    {
        "status_code": 200,
        "status": "success",
        "message": "Authentication successful",
        "data": {
            "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
            "token_type": "bearer",
            "user": {
                "id": "uuid",
                "email": "user@example.com",
                "name": "John Doe",
                "wallet_number": "WAL123456789"
            }
        }
    }
    ```
    
    **Errors:**
    - 400: Missing or invalid authorization code
    - 401: Invalid code or token exchange failed
    - 500: Provider error or internal server error
    """
    try:
        # Validate code parameter
        if not code:
            raise HTTPException(
                status_code=400,
                detail={
                    "status_code": 400,
                    "status": "error",
                    "message": "Missing authorization code",
                    "data": None
                }
            )
        
        # Exchange authorization code for access token
        async with httpx.AsyncClient() as client:
            token_response = await client.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "code": code,
                    "client_id": settings.GOOGLE_CLIENT_ID,
                    "client_secret": settings.GOOGLE_CLIENT_SECRET,
                    "redirect_uri": settings.GOOGLE_REDIRECT_URI,
                    "grant_type": "authorization_code"
                }
            )
            
            if token_response.status_code != 200:
                raise HTTPException(
                    status_code=401,
                    detail={
                        "status_code": 401,
                        "status": "error",
                        "message": "Failed to exchange authorization code",
                        "data": None
                    }
                )
            
            token_data = token_response.json()
            access_token = token_data.get("access_token")
            
            # Fetch user info from Google
            userinfo_response = await client.get(
                "https://www.googleapis.com/oauth2/v2/userinfo",
                headers={"Authorization": f"Bearer {access_token}"}
            )
            
            if userinfo_response.status_code != 200:
                raise HTTPException(
                    status_code=401,
                    detail={
                        "status_code": 401,
                        "status": "error",
                        "message": "Failed to fetch user information from Google",
                        "data": None
                    }
                )
            
            google_info = userinfo_response.json()
        
        # Get or create user (with wallet)
        user, created = await AuthService.get_or_create_user(
            google_id=google_info['id'],
            email=google_info['email'],
            name=google_info.get('name', google_info['email']),
            db=db
        )
        
        # Load wallet relationship
        await db.refresh(user, ['wallet'])
        
        # Generate JWT for our app
        jwt_token = AuthService.generate_jwt(user.id)
        
        return {
            "status_code": 200,
            "status": "success",
            "message": "Authentication successful" if not created else "User created and authenticated",
            "data": {
                "access_token": jwt_token,
                "token_type": "bearer",
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "name": user.name,
                    "wallet_number": user.wallet.wallet_number if user.wallet else None
                }
            }
        }
    
    except HTTPException:
        raise
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
