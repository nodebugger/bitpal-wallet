from google.auth.transport import requests
from google.oauth2 import id_token
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.user import User
from app.models.wallet import Wallet
from app.core.security import create_access_token


class AuthService:
    """Service for handling authentication operations."""
    
    @staticmethod
    async def verify_google_token(token: str, client_id: str) -> dict:
        """
        Verify Google ID token.
        
        Args:
            token: Google ID token
            client_id: Google OAuth client ID
            
        Returns:
            dict: Decoded token with user info
            
        Raises:
            ValueError: If token is invalid
        """
        try:
            # Verify the token
            idinfo = id_token.verify_oauth2_token(
                token, requests.Request(), client_id
            )
            
            # Verify issuer
            if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
                raise ValueError('Invalid issuer')
            
            return idinfo
        except Exception as e:
            raise ValueError(f"Invalid Google token: {str(e)}")
    
    @staticmethod
    async def get_or_create_user(
        google_id: str,
        email: str,
        username: str,
        db: AsyncSession
    ) -> tuple[User, bool]:
        """
        Get existing user or create new one with wallet.
        
        Args:
            google_id: Google user ID
            email: User email
            username: User name
            db: Database session
            
        Returns:
            tuple: (User object, created flag)
        """
        # Check if user exists
        stmt = select(User).where(User.google_id == google_id)
        result = await db.execute(stmt)
        user = result.scalars().first()
        
        if user:
            return user, False
        
        # Create new user and wallet atomically
        async with db.begin_nested():
            # Create user
            user = User(
                google_id=google_id,
                email=email,
                username=username
            )
            db.add(user)
            await db.flush()
            
            # Create wallet for user
            wallet = Wallet(
                user_id=user.id,
                wallet_number=Wallet.generate_wallet_number()
            )
            db.add(wallet)
            await db.flush()
        
        await db.commit()
        await db.refresh(user)
        
        return user, True
    
    @staticmethod
    def generate_jwt(user_id: str) -> str:
        """
        Generate JWT token for user.
        
        Args:
            user_id: User ID
            
        Returns:
            str: JWT token
        """
        return create_access_token(user_id)
