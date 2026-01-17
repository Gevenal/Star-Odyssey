"""NPC AI agent."""
from typing import Any, Dict
from app.ai.agents.base_agent import BaseAgent


class NPCAgent(BaseAgent):
    """AI agent for individual NPC behavior."""

    def __init__(self, gemini_client, npc_id: str):
        """
        Initialize NPC agent.

        Args:
            gemini_client: GeminiClient instance
            npc_id: NPC identifier
        """
        super().__init__(gemini_client)
        self.npc_id = npc_id

    async def act(self, game_state, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate NPC action.

        Args:
            game_state: Current GameState
            context: Action context

        Returns:
            dict: NPC action (dialogue, movement, etc.)
        """
        raise NotImplementedError

    def can_act(self, game_state, context: Dict[str, Any]) -> bool:
        """Check if NPC can act."""
        raise NotImplementedError

    async def generate_dialogue(self, player_input: str, game_state) -> str:
        """
        Generate NPC dialogue response.

        Args:
            player_input: Player's message
            game_state: Current GameState

        Returns:
            str: NPC dialogue
        """
        raise NotImplementedError

    async def decide_action(self, game_state) -> Dict[str, Any]:
        """
        Decide NPC's autonomous action.

        Args:
            game_state: Current GameState

        Returns:
            dict: Chosen action
        """
        raise NotImplementedError
