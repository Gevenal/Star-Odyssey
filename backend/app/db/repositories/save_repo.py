"""Save game repository."""
from typing import Optional, Dict, Any, List
from app.db.repositories.base_repo import BaseRepository


class SaveRepository(BaseRepository):
    """Repository for saved games."""

    def __init__(self, db):
        """
        Initialize save repository.

        Args:
            db: Database instance
        """
        super().__init__(db, "saves")

    async def create(self, data: Dict[str, Any]) -> str:
        """Create new save."""
        raise NotImplementedError

    async def get(self, id: str) -> Optional[Dict[str, Any]]:
        """Get save by ID."""
        raise NotImplementedError

    async def update(self, id: str, data: Dict[str, Any]) -> bool:
        """Update save data."""
        raise NotImplementedError

    async def delete(self, id: str) -> bool:
        """Delete save."""
        raise NotImplementedError

    async def list_saves(self, player_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List all saves, optionally filtered by player.

        Args:
            player_id: Optional player identifier

        Returns:
            list[dict]: Save metadata
        """
        raise NotImplementedError

    async def get_save_by_name(self, save_name: str) -> Optional[Dict[str, Any]]:
        """
        Get save by name.

        Args:
            save_name: Save name

        Returns:
            Optional[dict]: Save data or None
        """
        raise NotImplementedError
