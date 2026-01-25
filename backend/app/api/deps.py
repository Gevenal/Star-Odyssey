"""Dependency injection for API routes."""
from motor.motor_asyncio import AsyncIOMotorClient
from app.core.session_state_manager import SessionStateManager
from app.core.game_state_manager import GameStateManager
from app.config import settings

# Global MongoDB client (initialized in main.py)
_mongo_client: AsyncIOMotorClient = None


def set_mongo_client(client: AsyncIOMotorClient):
    """Set MongoDB client (called during app startup)."""
    global _mongo_client
    _mongo_client = client


def get_mongo_client() -> AsyncIOMotorClient:
    """Get MongoDB client."""
    if _mongo_client is None:
        raise RuntimeError("MongoDB client not initialized. Call set_mongo_client() first.")
    return _mongo_client


def get_session_manager() -> SessionStateManager:
    """
    Get SessionStateManager for database operations.
    
    Returns:
        SessionStateManager: Database persistence manager
    """
    client = get_mongo_client()
    return SessionStateManager(client, redis_cache=None)


def get_game_state_manager_class():
    """
    Return the GameStateManager class (not instance).
    
    GameStateManager is typically instantiated inside GameLoop,
    not as a dependency. This function is provided for special cases.
    
    Returns:
        type: GameStateManager class
    """
    return GameStateManager

def get_gemini_client():
    """
    Get GeminiClient instance (placeholder).
    TODO Phase 1: Implement actual GeminiClient.
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="GeminiClient not yet implemented"
    )


def get_game_loop():
    """
    Get GameLoop instance (placeholder).
    TODO Phase 1: Implement actual GameLoop.
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="GameLoop not yet implemented"
    )