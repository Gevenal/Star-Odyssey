"""Game repository."""
from typing import Optional, Dict, Any
from app.db.repositories.base_repo import BaseRepository


class GameRepository(BaseRepository):
    """Repository for game session data."""

    def __init__(self, db):
        """
        Initialize game repository.

        Args:
            db: Database instance
        """
        super().__init__(db, "games")

    async def create(self, data: Dict[str, Any]) -> str:
        """Create new game session."""
        raise NotImplementedError

    async def get(self, id: str) -> Optional[Dict[str, Any]]:
        """Get game session by ID."""
        raise NotImplementedError

    async def update(self, id: str, data: Dict[str, Any]) -> bool:
        """Update game session."""
        raise NotImplementedError

    async def delete(self, id: str) -> bool:
        """Delete game session."""
        raise NotImplementedError

    async def get_by_session_id(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get game by session ID.

        Args:
            session_id: Session identifier

        Returns:
            Optional[dict]: Game data or None
        """
        raise NotImplementedError

    async def list_active_games(self) -> list[Dict[str, Any]]:
        """
        List all active game sessions.

        Returns:
            list[dict]: Active games
        """
        raise NotImplementedError
