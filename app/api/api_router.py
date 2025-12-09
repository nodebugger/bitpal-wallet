"""
API Router - Centralized router management for all API versions.

This file aggregates all route modules and provides a single entry point
for registering routes in the main application.
"""
from fastapi import APIRouter

from app.api.routes import general, auth

# API v1 router
api_v1_router = APIRouter(prefix="/api/v1")
api_v1_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
# Add more v1 routes here as they're created:
# api_v1_router.include_router(wallet.router, prefix="/wallet", tags=["Wallet"])
# api_v1_router.include_router(transfer.router, prefix="/transfers", tags=["Transfers"])
# api_v1_router.include_router(keys.router, prefix="/keys", tags=["API Keys"])


# General routes
general_router = APIRouter()
general_router.include_router(general.router, tags=["General"])


# Future: API v2 router (when needed)
# api_v2_router = APIRouter(prefix="/api/v2")
# api_v2_router.include_router(auth_v2.router, prefix="/auth", tags=["Authentication V2"])
