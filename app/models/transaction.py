"""Transaction model for tracking all wallet transactions."""
import uuid
from datetime import datetime
from decimal import Decimal
from sqlalchemy import Column, String, DateTime, ForeignKey, DECIMAL, Enum, Index
from sqlalchemy.orm import relationship
import enum

from app.db.session import Base


class TransactionType(str, enum.Enum):
    """Transaction types."""
    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"
    TRANSFER_IN = "transfer_in"
    TRANSFER_OUT = "transfer_out"


class TransactionStatus(str, enum.Enum):
    """Transaction statuses."""
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"


class Transaction(Base):
    """Transaction model for recording all wallet transactions."""
    
    __tablename__ = "transactions"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    wallet_id = Column(String(36), ForeignKey("wallets.id", ondelete="CASCADE"), nullable=False, index=True)
    type = Column(Enum(TransactionType), nullable=False)
    status = Column(Enum(TransactionStatus), default=TransactionStatus.PENDING, nullable=False)
    amount = Column(DECIMAL(precision=15, scale=2), nullable=False)
    reference = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(String(500), nullable=True)
    
    # For transfers - track counterparty
    counterparty_wallet_id = Column(String(36), ForeignKey("wallets.id"), nullable=True)
    
    # Paystack specific fields
    paystack_reference = Column(String(100), nullable=True, index=True)
    paystack_access_code = Column(String(100), nullable=True)
    authorization_url = Column(String(500), nullable=True)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    
    # Relationships
    wallet = relationship("Wallet", back_populates="transactions", foreign_keys=[wallet_id])
    
    # Indexes
    __table_args__ = (
        Index('ix_transactions_wallet_type', 'wallet_id', 'type'),
        Index('ix_transactions_wallet_status', 'wallet_id', 'status'),
    )
    
    def __repr__(self):
        return f"<Transaction {self.reference} - {self.type}: {self.amount}>"
    
    @staticmethod
    def generate_reference(prefix: str = "TXN") -> str:
        """Generate a unique transaction reference."""
        import time
        timestamp = int(time.time() * 1000)
        random_part = uuid.uuid4().hex[:8].upper()
        return f"{prefix}_{timestamp}_{random_part}"
    
    def to_dict(self):
        """Convert model to dictionary."""
        return {
            "id": self.id,
            "type": self.type.value if self.type else None,
            "status": self.status.value if self.status else None,
            "amount": float(self.amount) if self.amount else 0,
            "reference": self.reference,
            "description": self.description,
            "counterparty_wallet_id": self.counterparty_wallet_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }
