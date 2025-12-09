"""General routes (health check, root)."""
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db

router = APIRouter()


@router.get("/")
async def root():
    """Root endpoint."""
    return {
        "status_code": 200,
        "status": "success",
        "message": "Bitpal Wallet Service API",
        "data": {
            "version": "1.0.0",
            "docs": "/docs"
        }
    }


@router.get("/health")
async def health_check(db: AsyncSession = Depends(get_db)):
    """
    Health check endpoint to verify API and database connectivity.
    
    Returns:
        dict: Health status with database connection info
    """
    try:
        # Test database connection
        result = await db.execute(text("SELECT 1"))
        result.scalar()
        
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"
    
    return {
        "status_code": 200,
        "status": "success",
        "message": "Service is healthy",
        "data": {
            "api": "operational",
            "database": db_status
        }
    }
