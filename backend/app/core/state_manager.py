"""Game state management."""
from typing import Optional


class StateManager:
    """Manages game state storage and retrieval."""

    def __init__(self, state_repo, redis_cache):
        """
        Initialize state manager.

        Args:
            state_repo: StateRepository instance
            redis_cache: RedisCache instance
        """
        self.state_repo = state_repo
        self.redis_cache = redis_cache

    async def create_session(self, player_name: str) -> str:
        """
        Create a new game session.

        Args:
            player_name: Player's chosen name

        Returns:
            str: New session ID
        """
        raise NotImplementedError

    async def get_state(self, session_id: str):
        """
        Get game state by session ID.

        Args:
            session_id: Game session identifier

        Returns:
            GameState: Current game state
        """
        raise NotImplementedError

    async def update_state(self, session_id: str, state):
        """
        Update game state.

        Args:
            session_id: Game session identifier
            state: Updated GameState
        """
        raise NotImplementedError

    async def save_checkpoint(self, session_id: str):
        """
        Save a checkpoint of current state.

        Args:
            session_id: Game session identifier

        Returns:
            str: Checkpoint ID
        """
        raise NotImplementedError

    async def restore_checkpoint(self, checkpoint_id: str) -> str:
        """
        Restore from checkpoint.

        Args:
            checkpoint_id: Checkpoint identifier

        Returns:
            str: New session ID with restored state
        """
        raise NotImplementedError

    async def delete_session(self, session_id: str):
        """
        Delete a game session.

        Args:
            session_id: Game session identifier
        """
        raise NotImplementedError

    async def get_from_cache(self, session_id: str) -> Optional[dict]:
        """
        Get state from Redis cache.

        Args:
            session_id: Game session identifier

        Returns:
            Optional[dict]: Cached state or None
        """
        raise NotImplementedError

    async def set_cache(self, session_id: str, state_data: dict, ttl: int = 3600):
        """
        Set state in Redis cache.

        Args:
            session_id: Game session identifier
            state_data: State data to cache
            ttl: Time to live in seconds
        """
        raise NotImplementedError
