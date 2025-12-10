"""Wallet service for wallet operations."""
from datetime import datetime
from decimal import Decimal
from typing import List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.models.wallet import Wallet
from app.models.transaction import Transaction, TransactionType, TransactionStatus


class WalletService:
    """Service for handling wallet operations."""
    
    @staticmethod
    async def get_wallet_by_user_id(user_id: str, db: AsyncSession) -> Optional[Wallet]:
        """Get wallet by user ID."""
        stmt = select(Wallet).where(Wallet.user_id == user_id)
        result = await db.execute(stmt)
        return result.scalars().first()
    
    @staticmethod
    async def get_wallet_by_number(wallet_number: str, db: AsyncSession) -> Optional[Wallet]:
        """Get wallet by wallet number."""
        stmt = select(Wallet).where(Wallet.wallet_number == wallet_number)
        result = await db.execute(stmt)
        return result.scalars().first()
    
    @staticmethod
    async def get_balance(wallet: Wallet) -> dict:
        """Get wallet balance information."""
        return {
            "balance": float(wallet.balance),
            "wallet_number": wallet.wallet_number,
            "currency": wallet.currency
        }
    
    @staticmethod
    async def transfer(
        sender_wallet: Wallet,
        recipient_wallet_number: str,
        amount: Decimal,
        db: AsyncSession
    ) -> Tuple[Transaction, Transaction]:
        """
        Transfer funds between wallets.
        
        Args:
            sender_wallet: Sender's wallet
            recipient_wallet_number: Recipient's wallet number
            amount: Amount to transfer
            db: Database session
            
        Returns:
            tuple: (sender_transaction, recipient_transaction)
            
        Raises:
            ValueError: If transfer validation fails
        """
        # Validate amount
        if amount <= 0:
            raise ValueError("Transfer amount must be greater than zero")
        
        # Check sender balance
        if sender_wallet.balance < amount:
            raise ValueError("Insufficient balance")
        
        # Get recipient wallet
        recipient_wallet = await WalletService.get_wallet_by_number(recipient_wallet_number, db)
        if not recipient_wallet:
            raise ValueError("Recipient wallet not found")
        
        # Prevent self-transfer
        if sender_wallet.id == recipient_wallet.id:
            raise ValueError("Cannot transfer to your own wallet")
        
        # Generate references
        base_reference = Transaction.generate_reference("TRF")
        
        # Create sender transaction (debit)
        sender_txn = Transaction(
            wallet_id=sender_wallet.id,
            type=TransactionType.TRANSFER_OUT,
            status=TransactionStatus.SUCCESS,
            amount=amount,
            reference=f"{base_reference}_OUT",
            description=f"Transfer to wallet {recipient_wallet_number}",
            counterparty_wallet_id=recipient_wallet.id,
            completed_at=datetime.utcnow()
        )
        
        # Create recipient transaction (credit)
        recipient_txn = Transaction(
            wallet_id=recipient_wallet.id,
            type=TransactionType.TRANSFER_IN,
            status=TransactionStatus.SUCCESS,
            amount=amount,
            reference=f"{base_reference}_IN",
            description=f"Transfer from wallet {sender_wallet.wallet_number}",
            counterparty_wallet_id=sender_wallet.id,
            completed_at=datetime.utcnow()
        )
        
        # Atomic balance update
        sender_wallet.balance = sender_wallet.balance - amount
        recipient_wallet.balance = recipient_wallet.balance + amount
        
        # Add transactions
        db.add(sender_txn)
        db.add(recipient_txn)
        
        await db.commit()
        await db.refresh(sender_txn)
        await db.refresh(recipient_txn)
        
        return sender_txn, recipient_txn
    
    @staticmethod
    async def get_transactions(
        wallet: Wallet,
        db: AsyncSession,
        limit: int = 50,
        offset: int = 0
    ) -> List[Transaction]:
        """Get transaction history for a wallet."""
        stmt = (
            select(Transaction)
            .where(Transaction.wallet_id == wallet.id)
            .order_by(Transaction.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())
    
    @staticmethod
    async def get_transaction_by_reference(
        reference: str,
        wallet: Wallet,
        db: AsyncSession
    ) -> Optional[Transaction]:
        """Get a specific transaction by reference."""
        stmt = select(Transaction).where(
            and_(
                Transaction.wallet_id == wallet.id,
                Transaction.reference == reference
            )
        )
        result = await db.execute(stmt)
        return result.scalars().first()
