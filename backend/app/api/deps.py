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
    """Get GeminiClient singleton."""
    from app.ai.gemini_client import get_gemini_client as _get
    return _get()


def get_rules_engine():
    """Get a RulesEngine with ResourceAvailability and LocationTopology rules wired to GameDataLoader."""
    from app.core.rules.engine import RulesEngine
    from app.game_data.loader import get_game_data_loader
    return RulesEngine(game_data_loader=get_game_data_loader())


def get_game_data_loader():
    """Get GameDataLoader singleton."""
    from app.game_data.loader import get_game_data_loader as _get
    return _get()


def get_game_loop():
    """Get GameLoop wired to SessionStateManager, RulesEngine, GeminiClient, and GameDataLoader."""
    from app.core.game_loop import GameLoop
    return GameLoop(
        state_manager=get_session_manager(),
        rules_engine=get_rules_engine(),
        gemini_client=get_gemini_client(),
        game_data_loader=get_game_data_loader(),
    )