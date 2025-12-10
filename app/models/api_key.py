"""API Key model for service-to-service authentication."""
import uuid
import secrets
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean, JSON
from sqlalchemy.orm import relationship

from app.db.session import Base


class APIKey(Base):
    """API Key model for storing service API keys."""
    
    __tablename__ = "api_keys"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    key_hash = Column(String(255), unique=True, nullable=False, index=True)  # Hashed API key for lookup
    key_prefix = Column(String(10), nullable=False)  # First few chars for display (sk_live_xxx...)
    permissions = Column(JSON, nullable=False, default=list)  # ["deposit", "transfer", "read"]
    expires_at = Column(DateTime, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_revoked = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_used_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="api_keys")
    
    def __repr__(self):
        return f"<APIKey {self.key_prefix}*** - User: {self.user_id}>"
    
    @staticmethod
    def generate_api_key() -> tuple[str, str, str]:
        """
        Generate a new API key.
        
        Returns:
            tuple: (full_key, key_prefix, key_hash)
        """
        # Generate a secure random key
        random_part = secrets.token_urlsafe(32)
        full_key = f"sk_live_{random_part}"
        key_prefix = full_key[:15]  # sk_live_xxxxx
        
        # Hash the full key for storage
        import hashlib
        key_hash = hashlib.sha256(full_key.encode()).hexdigest()
        
        return full_key, key_prefix, key_hash
    
    @staticmethod
    def hash_key(api_key: str) -> str:
        """Hash an API key for comparison."""
        import hashlib
        return hashlib.sha256(api_key.encode()).hexdigest()
    
    def is_expired(self) -> bool:
        """Check if the API key is expired."""
        return datetime.utcnow() > self.expires_at
    
    def has_permission(self, permission: str) -> bool:
        """Check if the API key has a specific permission."""
        return permission in self.permissions
    
    def to_dict(self, include_key: bool = False):
        """Convert model to dictionary."""
        data = {
            "id": self.id,
            "name": self.name,
            "key_prefix": self.key_prefix,
            "permissions": self.permissions,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "is_active": self.is_active,
            "is_revoked": self.is_revoked,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_used_at": self.last_used_at.isoformat() if self.last_used_at else None,
        }
        return data
