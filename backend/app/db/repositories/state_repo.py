"""Game state repository."""
from typing import Optional, Dict, Any, List
from app.db.repositories.base_repo import BaseRepository


class StateRepository(BaseRepository):
    """Repository for game state data."""

    def __init__(self, db):
        """
        Initialize state repository.

        Args:
            db: Database instance
        """
        super().__init__(db, "states")

    async def create(self, data: Dict[str, Any]) -> str:
        """Create new game state."""
        raise NotImplementedError

    async def get(self, id: str) -> Optional[Dict[str, Any]]:
        """Get game state by ID."""
        raise NotImplementedError

    async def update(self, id: str, data: Dict[str, Any]) -> bool:
        """Update game state."""
        raise NotImplementedError

    async def delete(self, id: str) -> bool:
        """Delete game state."""
        raise NotImplementedError

    async def get_latest_by_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get latest state for session.

        Args:
            session_id: Session identifier

        Returns:
            Optional[dict]: Latest state or None
        """
        raise NotImplementedError

    async def get_state_history(self, session_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get state history for session.

        Args:
            session_id: Session identifier
            limit: Number of states to retrieve

        Returns:
            list[dict]: State history
        """
        raise NotImplementedError

    async def create_checkpoint(self, session_id: str, state_data: Dict[str, Any]) -> str:
        """
        Create state checkpoint.

        Args:
            session_id: Session identifier
            state_data: State to checkpoint

        Returns:
            str: Checkpoint ID
        """
        raise NotImplementedError
