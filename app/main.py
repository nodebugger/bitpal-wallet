"""Main FastAPI application with lifespan management."""
from contextlib import asynccontextmanager
from fastapi import FastAPI
import logging

from app.core.config import settings
from app.api.api_router import api_v1_router, general_router
from app.db.session import engine

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events."""
    # Startup
    logger.info("🚀 Starting up Bitpal Wallet Service...")
    logger.info(f"📦 Database: {settings.DATABASE_URL.split('@')[1] if '@' in settings.DATABASE_URL else 'configured'}")
    logger.info(f"🔐 JWT Algorithm: {settings.ALGORITHM}")
    logger.info(f"⏱️  Token Expiry: {settings.ACCESS_TOKEN_EXPIRE_MINUTES} minutes")
    
    # Test database connection
    try:
        async with engine.connect() as conn:
            logger.info("✅ Database connection established")
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down Bitpal Wallet Service...")
    await engine.dispose()
    logger.info("✅ Database connections closed")


app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    debug=settings.DEBUG,
    description="Bitpal Wallet Service - Secure digital wallet with Paystack integration",
    lifespan=lifespan,
)

# Register routers
app.include_router(general_router)
app.include_router(api_v1_router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
