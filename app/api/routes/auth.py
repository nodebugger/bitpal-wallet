"""Authentication endpoints."""
from typing import Optional
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
async def google_sign_in():
    """
    **Step 1: Trigger Google OAuth sign-in flow**
    w
    Returns the Google OAuth URL as JSON.
    
    **Usage:**
    - API/Mobile/Swagger: `GET /api/v1/auth/google` → Returns JSON with URL
    - Open the returned URL in a browser to complete authentication
    
    **Response:**
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
    
    **Note:** Redirect option removed as it doesn't work with Swagger/API clients due to CORS.
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
    code: Optional[str] = Query(None, description="Authorization code from Google"),
    error: Optional[str] = Query(None, description="Error code if authorization failed"),
    error_description: Optional[str] = Query(None, description="Human-readable error description"),
    db: AsyncSession = Depends(get_db)
):
    """
    **Step 2: Google OAuth callback endpoint**
    
    Receives the authorization code from Google after user consent.
    Exchanges code for access token, fetches user info, and creates/updates user.
    
    **This endpoint is called by Google, not by your frontend directly.**
    
    **Query Parameters:**
    - code (optional): Authorization code from Google (present on success)
    - error (optional): Error code if user denied or authorization failed
    - error_description (optional): Human-readable error description
    
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
    - 400: User denied access or missing authorization code
    - 401: Invalid code or token exchange failed
    - 500: Provider error or internal server error
    """
    try:
        # Check if Google returned an error (user denied, invalid config, etc.)
        if error:
            error_messages = {
                "access_denied": "User denied access to their Google account",
                "invalid_request": "Invalid OAuth request configuration",
                "unauthorized_client": "Client not authorized for this request",
                "unsupported_response_type": "Invalid response_type parameter",
                "invalid_scope": "Invalid scope requested",
                "server_error": "Google OAuth server error",
                "temporarily_unavailable": "Google OAuth temporarily unavailable"
            }
            
            message = error_messages.get(error, f"OAuth error: {error}")
            if error_description:
                message += f". {error_description}"
            
            raise HTTPException(
                status_code=400,
                detail={
                    "status_code": 400,
                    "status": "error",
                    "message": message,
                    "data": {"error": error, "error_description": error_description}
                }
            )
        
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
        # Log the actual error for debugging
        import traceback
        print(f"❌ OAuth callback error: {str(e)}")
        print(traceback.format_exc())
        
        raise HTTPException(
            status_code=500,
            detail={
                "status_code": 500,
                "status": "error",
                "message": f"Authentication failed: {str(e)}",
                "data": None
            }
        )
