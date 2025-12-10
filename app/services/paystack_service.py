"""Paystack integration service."""
import hashlib
import hmac
from datetime import datetime
from decimal import Decimal
from typing import Optional, Tuple
import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.core.config import settings
from app.models.wallet import Wallet
from app.models.transaction import Transaction, TransactionType, TransactionStatus


class PaystackService:
    """Service for handling Paystack payment operations."""
    
    BASE_URL = "https://api.paystack.co"
    
    @staticmethod
    def get_headers() -> dict:
        """Get headers for Paystack API requests."""
        return {
            "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
            "Content-Type": "application/json"
        }
    
    @staticmethod
    async def initialize_transaction(
        email: str,
        amount: int,  # Amount in kobo (smallest currency unit)
        reference: str,
        callback_url: Optional[str] = None
    ) -> dict:
        """
        Initialize a Paystack transaction.
        
        Args:
            email: Customer email
            amount: Amount in kobo (e.g., 5000 Naira = 500000 kobo)
            reference: Unique transaction reference
            callback_url: Optional callback URL after payment
            
        Returns:
            dict: Paystack response with authorization_url
            
        Raises:
            Exception: If Paystack API call fails
        """
        payload = {
            "email": email,
            "amount": amount,
            "reference": reference,
            "currency": "NGN"
        }
        
        if callback_url:
            payload["callback_url"] = callback_url
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{PaystackService.BASE_URL}/transaction/initialize",
                json=payload,
                headers=PaystackService.get_headers()
            )
            
            data = response.json()
            
            if not data.get("status"):
                raise Exception(data.get("message", "Failed to initialize Paystack transaction"))
            
            return data.get("data", {})
    
    @staticmethod
    async def verify_transaction(reference: str) -> dict:
        """
        Verify a Paystack transaction status.
        
        Args:
            reference: Transaction reference to verify
            
        Returns:
            dict: Transaction verification data
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{PaystackService.BASE_URL}/transaction/verify/{reference}",
                headers=PaystackService.get_headers()
            )
            
            data = response.json()
            
            if not data.get("status"):
                raise Exception(data.get("message", "Failed to verify transaction"))
            
            return data.get("data", {})
    
    @staticmethod
    def verify_webhook_signature(payload: bytes, signature: str) -> bool:
        """
        Verify Paystack webhook signature.
        
        Args:
            payload: Raw request body bytes
            signature: Signature from x-paystack-signature header
            
        Returns:
            bool: True if signature is valid
        """
        expected_signature = hmac.new(
            settings.PAYSTACK_SECRET_KEY.encode('utf-8'),
            payload,
            hashlib.sha512
        ).hexdigest()
        
        return hmac.compare_digest(expected_signature, signature)
    
    @staticmethod
    async def create_deposit_transaction(
        wallet: Wallet,
        amount: Decimal,
        email: str,
        db: AsyncSession
    ) -> Tuple[Transaction, dict]:
        """
        Create a deposit transaction and initialize Paystack payment.
        
        Args:
            wallet: User's wallet
            amount: Amount to deposit (in Naira)
            email: User's email
            db: Database session
            
        Returns:
            tuple: (Transaction, Paystack response data)
        """
        # Generate reference
        reference = Transaction.generate_reference("DEP")
        
        # Create transaction record
        transaction = Transaction(
            wallet_id=wallet.id,
            type=TransactionType.DEPOSIT,
            status=TransactionStatus.PENDING,
            amount=amount,
            reference=reference,
            paystack_reference=reference,
            description=f"Deposit of ₦{amount:,.2f}"
        )
        
        db.add(transaction)
        await db.flush()
        
        try:
            # Initialize Paystack transaction (amount in kobo)
            amount_in_kobo = int(amount * 100)
            paystack_data = await PaystackService.initialize_transaction(
                email=email,
                amount=amount_in_kobo,
                reference=reference
            )
            
            # Update transaction with Paystack data
            transaction.paystack_access_code = paystack_data.get("access_code")
            transaction.authorization_url = paystack_data.get("authorization_url")
            
            await db.commit()
            await db.refresh(transaction)
            
            return transaction, paystack_data
            
        except Exception as e:
            # Mark transaction as failed
            transaction.status = TransactionStatus.FAILED
            transaction.description = f"Failed to initialize payment: {str(e)}"
            await db.commit()
            raise
    
    @staticmethod
    async def process_webhook(
        event: str,
        data: dict,
        db: AsyncSession
    ) -> bool:
        """
        Process Paystack webhook event.
        
        Args:
            event: Event type (e.g., "charge.success")
            data: Event data
            db: Database session
            
        Returns:
            bool: True if processed successfully
        """
        if event != "charge.success":
            # Only handle successful charges
            return True
        
        reference = data.get("reference")
        if not reference:
            return False
        
        # Find the transaction - make it idempotent
        stmt = select(Transaction).where(Transaction.paystack_reference == reference)
        result = await db.execute(stmt)
        transaction = result.scalars().first()
        
        if not transaction:
            return False
        
        # Idempotency: If already processed, skip
        if transaction.status == TransactionStatus.SUCCESS:
            return True
        
        # Verify the payment status
        paystack_status = data.get("status")
        if paystack_status != "success":
            transaction.status = TransactionStatus.FAILED
            await db.commit()
            return True
        
        # Get the wallet and credit it
        wallet_stmt = select(Wallet).where(Wallet.id == transaction.wallet_id)
        wallet_result = await db.execute(wallet_stmt)
        wallet = wallet_result.scalars().first()
        
        if not wallet:
            return False
        
        # Credit the wallet (atomic operation)
        wallet.balance = wallet.balance + transaction.amount
        transaction.status = TransactionStatus.SUCCESS
        transaction.completed_at = datetime.utcnow()
        
        await db.commit()
        
        return True
    
    @staticmethod
    async def get_transaction_by_reference(
        reference: str,
        wallet_id: str,
        db: AsyncSession
    ) -> Optional[Transaction]:
        """Get a transaction by reference for a specific wallet."""
        stmt = select(Transaction).where(
            and_(
                Transaction.reference == reference,
                Transaction.wallet_id == wallet_id
            )
        )
        result = await db.execute(stmt)
        return result.scalars().first()
