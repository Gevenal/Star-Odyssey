"""Main API router aggregation."""

from fastapi import APIRouter
from app.api.v1 import game, save, debug

# Create main v1 API router
api_router = APIRouter()

# Include game endpoints
api_router.include_router(
    game.router,
    prefix="/game",
    tags=["Game"],
)

# Include save/load endpoints
api_router.include_router(
    save.router,
    prefix="/save",
    tags=["Save/Load"],
)

# Include debug endpoints (dev only)
api_router.include_router(
    debug.router,
    prefix="/debug",
    tags=["Debug (Dev Only)"],
)
