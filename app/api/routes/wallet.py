"""Wallet endpoints for deposits, transfers, and transactions."""
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, Request, Header
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field
from typing import Optional

from app.db.session import get_db
from app.core.dependencies import (
    AuthenticatedUser,
    get_current_user,
    require_deposit_permission,
    require_transfer_permission,
    require_read_permission
)
from app.services.wallet_service import WalletService
from app.services.paystack_service import PaystackService

router = APIRouter()


# Request/Response schemas
class DepositRequest(BaseModel):
    """Schema for deposit request."""
    amount: float = Field(..., gt=0, description="Amount to deposit in Naira")


class TransferRequest(BaseModel):
    """Schema for transfer request."""
    wallet_number: str = Field(..., min_length=10, description="Recipient wallet number")
    amount: float = Field(..., gt=0, description="Amount to transfer in Naira")


@router.post("/deposit")
async def deposit(
    request: DepositRequest,
    auth_user: AuthenticatedUser = Depends(require_deposit_permission),
    db: AsyncSession = Depends(get_db)
):
    """
    **Initiate a wallet deposit via Paystack**
    
    Creates a pending deposit transaction and returns Paystack payment link.
    
    **Authentication:** JWT or API key with `deposit` permission
    
    **Request Body:**
    ```json
    {
        "amount": 5000
    }
    ```
    
    **Response:**
    ```json
    {
        "status_code": 200,
        "status": "success",
        "message": "Deposit initiated",
        "data": {
            "reference": "DEP_1234567890_ABCD1234",
            "authorization_url": "https://paystack.co/checkout/..."
        }
    }
    ```
    
    **Flow:**
    1. User calls this endpoint with amount
    2. System creates pending transaction
    3. User is redirected to Paystack payment page
    4. After payment, Paystack sends webhook to credit wallet
    """
    try:
        # Get user's wallet
        wallet = await WalletService.get_wallet_by_user_id(auth_user.user.id, db)
        if not wallet:
            raise HTTPException(
                status_code=404,
                detail={
                    "status_code": 404,
                    "status": "error",
                    "message": "Wallet not found",
                    "data": None
                }
            )
        
        # Create deposit transaction and initialize Paystack
        amount = Decimal(str(request.amount))
        transaction, paystack_data = await PaystackService.create_deposit_transaction(
            wallet=wallet,
            amount=amount,
            email=auth_user.user.email,
            db=db
        )
        
        return {
            "status_code": 200,
            "status": "success",
            "message": "Deposit initiated. Complete payment at the authorization URL.",
            "data": {
                "reference": transaction.reference,
                "authorization_url": paystack_data.get("authorization_url")
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
                "message": f"Failed to initiate deposit: {str(e)}",
                "data": None
            }
        )


@router.post("/paystack/webhook")
async def paystack_webhook(
    request: Request,
    x_paystack_signature: str = Header(..., alias="x-paystack-signature"),
    db: AsyncSession = Depends(get_db)
):
    """
    **Paystack webhook endpoint**
    
    Receives transaction updates from Paystack and credits wallet on success.
    
    **Security:** Validates Paystack signature
    
    **IMPORTANT:** This endpoint is called by Paystack, not by users.
    Only the webhook is allowed to credit wallets.
    
    **Actions on charge.success:**
    1. Verify signature
    2. Find transaction by reference
    3. Update transaction status
    4. Credit wallet balance
    
    **Response:**
    ```json
    {
        "status": true
    }
    ```
    """
    try:
        # Get raw body for signature verification
        body = await request.body()
        
        # Verify Paystack signature
        if not PaystackService.verify_webhook_signature(body, x_paystack_signature):
            raise HTTPException(
                status_code=401,
                detail={"status": False, "message": "Invalid signature"}
            )
        
        # Parse payload
        payload = await request.json()
        event = payload.get("event")
        data = payload.get("data", {})
        
        # Process webhook
        success = await PaystackService.process_webhook(event, data, db)
        
        if success:
            return {"status": True}
        else:
            return {"status": False, "message": "Failed to process webhook"}
    
    except HTTPException:
        raise
    except Exception as e:
        # Always return 200 to Paystack to prevent retries
        return {"status": False, "message": str(e)}


@router.get("/deposit/{reference}/status")
async def get_deposit_status(
    reference: str,
    auth_user: AuthenticatedUser = Depends(require_read_permission),
    db: AsyncSession = Depends(get_db)
):
    """
    **Check deposit transaction status from our database**
    
    Returns the status of a deposit transaction from our records.
    
    **Authentication:** JWT or API key with `read` permission
    
    **WARNING:** This endpoint does NOT credit wallets.
    Only the Paystack webhook credits wallets.
    This only checks our database status.
    
    **Path Parameters:**
    - `reference` - Transaction reference
    
    **Response:**
    ```json
    {
        "status_code": 200,
        "status": "success",
        "message": "Transaction status retrieved",
        "data": {
            "reference": "DEP_1234567890_ABCD1234",
            "status": "success|failed|pending",
            "amount": 5000
        }
    }
    ```
    """
    try:
        # Get user's wallet
        wallet = await WalletService.get_wallet_by_user_id(auth_user.user.id, db)
        if not wallet:
            raise HTTPException(
                status_code=404,
                detail={
                    "status_code": 404,
                    "status": "error",
                    "message": "Wallet not found",
                    "data": None
                }
            )
        
        # Get transaction
        transaction = await WalletService.get_transaction_by_reference(reference, wallet, db)
        if not transaction:
            raise HTTPException(
                status_code=404,
                detail={
                    "status_code": 404,
                    "status": "error",
                    "message": "Transaction not found",
                    "data": None
                }
            )
        
        return {
            "status_code": 200,
            "status": "success",
            "message": "Transaction status retrieved",
            "data": {
                "reference": transaction.reference,
                "status": transaction.status.value,
                "amount": float(transaction.amount)
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
                "message": "Failed to get transaction status",
                "data": None
            }
        )


@router.get("/deposit/{reference}/verify")
async def verify_deposit_with_paystack(
    reference: str,
    auth_user: AuthenticatedUser = Depends(require_read_permission),
    db: AsyncSession = Depends(get_db)
):
    """
    **Verify deposit transaction status directly from Paystack**
    
    Queries Paystack API to verify the actual payment status.
    This does NOT update the wallet - only the webhook does that.
    
    **Authentication:** JWT or API key with `read` permission
    
    **Use Case:** Check if Paystack has processed a payment when webhook hasn't arrived yet.
    
    **Path Parameters:**
    - `reference` - Transaction reference
    """
    try:
        # Get user's wallet
        wallet = await WalletService.get_wallet_by_user_id(auth_user.user.id, db)
        if not wallet:
            raise HTTPException(
                status_code=404,
                detail={
                    "status_code": 404,
                    "status": "error",
                    "message": "Wallet not found",
                    "data": None
                }
            )
        
        # Get transaction from our database
        transaction = await WalletService.get_transaction_by_reference(reference, wallet, db)
        if not transaction:
            raise HTTPException(
                status_code=404,
                detail={
                    "status_code": 404,
                    "status": "error",
                    "message": "Transaction not found in our records",
                    "data": None
                }
            )
        
        # Verify with Paystack
        try:
            paystack_data = await PaystackService.verify_transaction(reference)
            
            return {
                "status_code": 200,
                "status": "success",
                "message": "Transaction verified with Paystack",
                "data": {
                    "reference": reference,
                    "paystack_status": paystack_data.get("status"),
                    "amount": paystack_data.get("amount", 0) / 100,  # Convert from kobo to naira
                    "paid_at": paystack_data.get("paid_at"),
                    "channel": paystack_data.get("channel"),
                    "currency": paystack_data.get("currency"),
                    "our_status": transaction.status.value,
                    "note": "Webhook will credit wallet automatically if payment succeeded"
                }
            }
        except Exception as paystack_error:
            # Paystack API failed, return our status with error note
            return {
                "status_code": 200,
                "status": "success",
                "message": "Could not verify with Paystack, showing our status",
                "data": {
                    "reference": reference,
                    "our_status": transaction.status.value,
                    "amount": float(transaction.amount),
                    "paystack_error": str(paystack_error),
                    "note": "Paystack verification failed. Check Paystack dashboard or wait for webhook."
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
                "message": f"Failed to verify transaction: {str(e)}",
                "data": None
            }
        )


@router.get("/balance")
async def get_balance(
    auth_user: AuthenticatedUser = Depends(require_read_permission),
    db: AsyncSession = Depends(get_db)
):
    """
    **Get wallet balance**
    
    Returns the current wallet balance.
    
    **Authentication:** JWT or API key with `read` permission
    
    **Response:**
    ```json
    {
        "status_code": 200,
        "status": "success",
        "message": "Balance retrieved",
        "data": {
            "balance": 15000
        }
    }
    ```
    """
    try:
        # Get user's wallet
        wallet = await WalletService.get_wallet_by_user_id(auth_user.user.id, db)
        if not wallet:
            raise HTTPException(
                status_code=404,
                detail={
                    "status_code": 404,
                    "status": "error",
                    "message": "Wallet not found",
                    "data": None
                }
            )
        
        return {
            "status_code": 200,
            "status": "success",
            "message": "Balance retrieved",
            "data": {
                "balance": float(wallet.balance)
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
                "message": "Failed to retrieve balance",
                "data": None
            }
        )


@router.post("/transfer")
async def transfer(
    request: TransferRequest,
    auth_user: AuthenticatedUser = Depends(require_transfer_permission),
    db: AsyncSession = Depends(get_db)
):
    """
    **Transfer funds to another wallet**
    
    Transfers money from your wallet to another user's wallet.
    
    **Authentication:** JWT or API key with `transfer` permission
    
    **Request Body:**
    ```json
    {
        "wallet_number": "4566678954356",
        "amount": 3000
    }
    ```
    
    **Response:**
    ```json
    {
        "status_code": 200,
        "status": "success",
        "message": "Transfer completed",
        "data": {
            "reference": "TRF_1234567890_ABCD1234_OUT",
            "amount": 3000,
            "recipient_wallet": "4566678954356"
        }
    }
    ```
    
    **Validations:**
    - Sender must have sufficient balance
    - Recipient wallet must exist
    - Cannot transfer to own wallet
    """
    try:
        # Get sender's wallet
        sender_wallet = await WalletService.get_wallet_by_user_id(auth_user.user.id, db)
        if not sender_wallet:
            raise HTTPException(
                status_code=404,
                detail={
                    "status_code": 404,
                    "status": "error",
                    "message": "Wallet not found",
                    "data": None
                }
            )
        
        # Perform transfer
        amount = Decimal(str(request.amount))
        sender_txn, _ = await WalletService.transfer(
            sender_wallet=sender_wallet,
            recipient_wallet_number=request.wallet_number,
            amount=amount,
            db=db
        )
        
        return {
            "status_code": 200,
            "status": "success",
            "message": "Transfer completed",
            "data": {
                "reference": sender_txn.reference,
                "amount": float(sender_txn.amount),
                "recipient_wallet": request.wallet_number
            }
        }
    
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail={
                "status_code": 400,
                "status": "error",
                "message": str(e),
                "data": None
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "status_code": 500,
                "status": "error",
                "message": "Transfer failed",
                "data": None
            }
        )


@router.get("/transactions")
async def get_transactions(
    auth_user: AuthenticatedUser = Depends(require_read_permission),
    db: AsyncSession = Depends(get_db),
    limit: int = 50,
    offset: int = 0
):
    """
    **Get transaction history**
    
    Returns the transaction history for the wallet.
    
    **Authentication:** JWT or API key with `read` permission
    
    **Query Parameters:**
    - `limit` - Maximum transactions to return (default: 50)
    - `offset` - Pagination offset (default: 0)
    
    **Response:**
    ```json
    {
        "status_code": 200,
        "status": "success",
        "message": "Transactions retrieved",
        "data": [
            {
                "type": "deposit",
                "amount": 5000,
                "status": "success"
            },
            {
                "type": "transfer_out",
                "amount": 3000,
                "status": "success"
            }
        ]
    }
    ```
    """
    try:
        # Get user's wallet
        wallet = await WalletService.get_wallet_by_user_id(auth_user.user.id, db)
        if not wallet:
            raise HTTPException(
                status_code=404,
                detail={
                    "status_code": 404,
                    "status": "error",
                    "message": "Wallet not found",
                    "data": None
                }
            )
        
        # Get transactions
        transactions = await WalletService.get_transactions(wallet, db, limit, offset)
        
        return {
            "status_code": 200,
            "status": "success",
            "message": "Transactions retrieved",
            "data": [
                {
                    "type": t.type.value,
                    "amount": float(t.amount),
                    "status": t.status.value,
                    "reference": t.reference,
                    "description": t.description,
                    "created_at": t.created_at.isoformat() if t.created_at else None
                }
                for t in transactions
            ]
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "status_code": 500,
                "status": "error",
                "message": "Failed to retrieve transactions",
                "data": None
            }
        )
