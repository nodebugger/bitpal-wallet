from datetime import datetime
from pydantic import BaseModel, Field
from decimal import Decimal


class WalletBase(BaseModel):
    """Base wallet schema."""
    wallet_number: str
    balance: float
    currency: str = "NGN"


class WalletResponse(WalletBase):
    """Schema for wallet response."""
    id: str
    user_id: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class BalanceResponse(BaseModel):
    """Schema for balance response."""
    balance: float
    wallet_number: str
    currency: str = "NGN"
