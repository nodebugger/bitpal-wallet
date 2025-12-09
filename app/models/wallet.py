"""Wallet model."""
import uuid
import random
from datetime import datetime
from decimal import Decimal
from sqlalchemy import Column, String, DateTime, ForeignKey, DECIMAL, CheckConstraint
from sqlalchemy.orm import relationship

from app.db.session import Base


class Wallet(Base):
    """Wallet model for storing user wallet information."""
    
    __tablename__ = "wallets"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    wallet_number = Column(String(13), unique=True, nullable=False, index=True)
    balance = Column(DECIMAL(precision=15, scale=2), default=Decimal("0.00"), nullable=False)
    currency = Column(String(3), default="NGN", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Constraints
    __table_args__ = (
        CheckConstraint('balance >= 0', name='positive_balance'),
    )
    
    # Relationships
    user = relationship("User", back_populates="wallet")
    transactions = relationship("Transaction", back_populates="wallet", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Wallet {self.wallet_number} - Balance: {self.balance}>"
    
    @staticmethod
    def generate_wallet_number() -> str:
        """Generate a unique 13-digit wallet number."""
        return str(random.randint(1000000000000, 9999999999999))
    
    def to_dict(self):
        """Convert model to dictionary."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "wallet_number": self.wallet_number,
            "balance": float(self.balance),
            "currency": self.currency,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
