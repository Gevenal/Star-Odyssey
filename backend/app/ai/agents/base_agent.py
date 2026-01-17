"""Base agent abstraction."""
from abc import ABC, abstractmethod
from typing import Any, Dict


class BaseAgent(ABC):
    """Abstract base class for AI agents."""

    def __init__(self, gemini_client):
        """
        Initialize agent.

        Args:
            gemini_client: GeminiClient instance
        """
        self.gemini_client = gemini_client

    @abstractmethod
    async def act(self, game_state, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform agent action.

        Args:
            game_state: Current GameState
            context: Action context

        Returns:
            dict: Action result
        """
        pass

    @abstractmethod
    def can_act(self, game_state, context: Dict[str, Any]) -> bool:
        """
        Check if agent can act in current state.

        Args:
            game_state: Current GameState
            context: Action context

        Returns:
            bool: True if agent can act
        """
        pass

    def get_priority(self) -> int:
        """
        Get agent priority for execution order.

        Returns:
            int: Priority (higher = earlier execution)
        """
        return 0
