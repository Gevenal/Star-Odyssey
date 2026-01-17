"""NPC repository."""
from typing import Optional, Dict, Any, List
from app.db.repositories.base_repo import BaseRepository


class NPCRepository(BaseRepository):
    """Repository for NPC data."""

    def __init__(self, db):
        """
        Initialize NPC repository.

        Args:
            db: Database instance
        """
        super().__init__(db, "npcs")

    async def create(self, data: Dict[str, Any]) -> str:
        """Create new NPC."""
        raise NotImplementedError

    async def get(self, id: str) -> Optional[Dict[str, Any]]:
        """Get NPC by ID."""
        raise NotImplementedError

    async def update(self, id: str, data: Dict[str, Any]) -> bool:
        """Update NPC data."""
        raise NotImplementedError

    async def delete(self, id: str) -> bool:
        """Delete NPC."""
        raise NotImplementedError

    async def get_by_session(self, session_id: str) -> List[Dict[str, Any]]:
        """
        Get all NPCs for session.

        Args:
            session_id: Session identifier

        Returns:
            list[dict]: NPCs in session
        """
        raise NotImplementedError

    async def get_by_location(self, session_id: str, location_id: str) -> List[Dict[str, Any]]:
        """
        Get NPCs at location.

        Args:
            session_id: Session identifier
            location_id: Location identifier

        Returns:
            list[dict]: NPCs at location
        """
        raise NotImplementedError

    async def update_relationship(self, npc_id: str, trust_delta: float) -> bool:
        """
        Update NPC relationship/trust level.

        Args:
            npc_id: NPC identifier
            trust_delta: Change in trust level

        Returns:
            bool: True if updated
        """
        raise NotImplementedError
