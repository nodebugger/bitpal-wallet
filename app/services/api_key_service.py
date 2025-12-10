"""API Key service for managing API keys."""
from datetime import datetime, timedelta
from typing import Optional, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func

from app.models.api_key import APIKey
from app.models.user import User


class APIKeyService:
    """Service for handling API key operations."""
    
    # Maximum active API keys per user
    MAX_ACTIVE_KEYS = 5
    
    # Expiry duration mapping
    EXPIRY_MAPPING = {
        "1H": timedelta(hours=1),
        "1D": timedelta(days=1),
        "1M": timedelta(days=30),
        "1Y": timedelta(days=365),
    }
    
    @staticmethod
    def calculate_expiry(expiry_code: str) -> datetime:
        """
        Calculate expiration datetime from expiry code.
        
        Args:
            expiry_code: One of 1H, 1D, 1M, 1Y
            
        Returns:
            datetime: Expiration datetime
        """
        delta = APIKeyService.EXPIRY_MAPPING.get(expiry_code)
        if not delta:
            raise ValueError(f"Invalid expiry code: {expiry_code}")
        return datetime.utcnow() + delta
    
    @staticmethod
    async def get_active_key_count(user_id: str, db: AsyncSession) -> int:
        """Get count of active (non-expired, non-revoked) API keys for user."""
        stmt = select(func.count(APIKey.id)).where(
            and_(
                APIKey.user_id == user_id,
                APIKey.is_active == True,
                APIKey.is_revoked == False,
                APIKey.expires_at > datetime.utcnow()
            )
        )
        result = await db.execute(stmt)
        return result.scalar() or 0
    
    @staticmethod
    async def create_api_key(
        user_id: str,
        name: str,
        permissions: List[str],
        expiry: str,
        db: AsyncSession
    ) -> Tuple[APIKey, str]:
        """
        Create a new API key for a user.
        
        Args:
            user_id: User ID
            name: Name for the API key
            permissions: List of permissions
            expiry: Expiry code (1H, 1D, 1M, 1Y)
            db: Database session
            
        Returns:
            tuple: (APIKey model, full_api_key)
            
        Raises:
            ValueError: If max keys limit reached or invalid expiry
        """
        # Check active key count
        active_count = await APIKeyService.get_active_key_count(user_id, db)
        if active_count >= APIKeyService.MAX_ACTIVE_KEYS:
            raise ValueError(f"Maximum {APIKeyService.MAX_ACTIVE_KEYS} active API keys allowed per user")
        
        # Generate new API key
        full_key, key_prefix, key_hash = APIKey.generate_api_key()
        
        # Calculate expiration
        expires_at = APIKeyService.calculate_expiry(expiry)
        
        # Create API key record
        api_key = APIKey(
            user_id=user_id,
            name=name,
            key_hash=key_hash,
            key_prefix=key_prefix,
            permissions=permissions,
            expires_at=expires_at,
            is_active=True,
            is_revoked=False
        )
        
        db.add(api_key)
        await db.commit()
        await db.refresh(api_key)
        
        # Ensure expires_at is loaded before returning
        _ = api_key.expires_at
        
        return api_key, full_key
    
    @staticmethod
    async def get_api_key_by_id(key_id: str, user_id: str, db: AsyncSession) -> Optional[APIKey]:
        """Get API key by ID for a specific user."""
        stmt = select(APIKey).where(
            and_(
                APIKey.id == key_id,
                APIKey.user_id == user_id
            )
        )
        result = await db.execute(stmt)
        return result.scalars().first()
    
    @staticmethod
    async def verify_api_key(api_key: str, db: AsyncSession) -> Optional[Tuple[APIKey, User]]:
        """
        Verify an API key and return the key and associated user.
        
        Args:
            api_key: The full API key to verify
            db: Database session
            
        Returns:
            tuple: (APIKey, User) if valid, None if invalid
        """
        # Hash the provided key
        key_hash = APIKey.hash_key(api_key)
        
        # Find the key
        stmt = select(APIKey).where(APIKey.key_hash == key_hash)
        result = await db.execute(stmt)
        api_key_obj = result.scalars().first()
        
        if not api_key_obj:
            return None
        
        # Check if key is valid
        if api_key_obj.is_revoked:
            return None
        
        if not api_key_obj.is_active:
            return None
        
        # Check expiration and mark as inactive if expired
        if api_key_obj.is_expired():
            api_key_obj.is_active = False
            await db.commit()
            return None
        
        # Update last used timestamp
        api_key_obj.last_used_at = datetime.utcnow()
        
        # Get associated user
        user_stmt = select(User).where(User.id == api_key_obj.user_id)
        user_result = await db.execute(user_stmt)
        user = user_result.scalars().first()
        
        if not user:
            return None
        
        await db.commit()
        
        return api_key_obj, user
    
    @staticmethod
    async def rollover_api_key(
        expired_key_id: str,
        user_id: str,
        new_expiry: str,
        db: AsyncSession
    ) -> Tuple[APIKey, str]:
        """
        Create a new API key with same permissions as an expired key.
        
        Args:
            expired_key_id: ID of the expired key
            user_id: User ID
            new_expiry: New expiry code
            db: Database session
            
        Returns:
            tuple: (new APIKey, full_api_key)
            
        Raises:
            ValueError: If key not found, not expired, or max limit reached
        """
        # Get the expired key
        expired_key = await APIKeyService.get_api_key_by_id(expired_key_id, user_id, db)
        
        if not expired_key:
            raise ValueError("API key not found")
        
        if not expired_key.is_expired():
            raise ValueError("API key is not expired. Only expired keys can be rolled over.")
        
        # Check active key count
        active_count = await APIKeyService.get_active_key_count(user_id, db)
        if active_count >= APIKeyService.MAX_ACTIVE_KEYS:
            raise ValueError(f"Maximum {APIKeyService.MAX_ACTIVE_KEYS} active API keys allowed per user")
        
        # Create new key with same permissions
        new_key, full_key = await APIKeyService.create_api_key(
            user_id=user_id,
            name=f"{expired_key.name} (rolled over)",
            permissions=expired_key.permissions,
            expiry=new_expiry,
            db=db
        )
        
        # Mark old key as inactive
        expired_key.is_active = False
        await db.commit()
        
        return new_key, full_key
    
    @staticmethod
    async def revoke_api_key(key_id: str, user_id: str, db: AsyncSession) -> bool:
        """
        Revoke an API key.
        
        Args:
            key_id: API key ID
            user_id: User ID
            db: Database session
            
        Returns:
            bool: True if revoked successfully
        """
        api_key = await APIKeyService.get_api_key_by_id(key_id, user_id, db)
        
        if not api_key:
            return False
        
        api_key.is_revoked = True
        api_key.is_active = False
        await db.commit()
        
        return True
    
    @staticmethod
    async def mark_expired_keys_inactive(user_id: str, db: AsyncSession) -> int:
        """
        Mark all expired keys as inactive for a user.
        
        Args:
            user_id: User ID
            db: Database session
            
        Returns:
            int: Number of keys marked as inactive
        """
        stmt = select(APIKey).where(
            and_(
                APIKey.user_id == user_id,
                APIKey.is_active == True,
                APIKey.expires_at <= datetime.utcnow()
            )
        )
        result = await db.execute(stmt)
        expired_keys = result.scalars().all()
        
        count = 0
        for key in expired_keys:
            key.is_active = False
            count += 1
        
        if count > 0:
            await db.commit()
        
        return count
    
    @staticmethod
    async def list_user_api_keys(user_id: str, db: AsyncSession) -> List[APIKey]:
        """
        Get all API keys for a user.
        Also marks expired keys as inactive automatically.
        """
        # First, mark any expired keys as inactive
        await APIKeyService.mark_expired_keys_inactive(user_id, db)
        
        # Then retrieve all keys
        stmt = select(APIKey).where(APIKey.user_id == user_id).order_by(APIKey.created_at.desc())
        result = await db.execute(stmt)
        return list(result.scalars().all())
