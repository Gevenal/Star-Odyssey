"""Game loop orchestration."""
from typing import AsyncGenerator


class GameLoop:
    """Orchestrates the turn-based game loop."""

    def __init__(self, state_manager, rules_engine, gemini_client):
        """
        Initialize game loop with dependencies.

        Args:
            state_manager: StateManager instance
            rules_engine: RulesEngine instance
            gemini_client: GeminiClient instance
        """
        self.state_manager = state_manager
        self.rules_engine = rules_engine
        self.gemini_client = gemini_client

    async def initialize(self, player_name: str):
        """
        Start a new game session.

        Args:
            player_name: Player's chosen name

        Returns:
            GameState: Initial game state with session ID
        """
        raise NotImplementedError

    async def process_action(self, session_id: str, action: str):
        """
        Process player action and return response.

        Args:
            session_id: Game session identifier
            action: Player action text

        Returns:
            GameActionResponse: Response with narration and updated state
        """
        raise NotImplementedError

    async def process_action_stream(self, session_id: str, action: str) -> AsyncGenerator[str, None]:
        """
        Process action with streaming response.

        Args:
            session_id: Game session identifier
            action: Player action text

        Yields:
            str: Narration chunks as they're generated
        """
        raise NotImplementedError
        # Make this a proper async generator
        yield ""

    async def get_state(self, session_id: str):
        """
        Get current game state.

        Args:
            session_id: Game session identifier

        Returns:
            GameState: Current game state
        """
        raise NotImplementedError

    async def advance_turn(self, session_id: str):
        """
        Advance to next turn (NPC actions, world events).

        Args:
            session_id: Game session identifier

        Returns:
            TurnResult: Results of turn advancement
        """
        raise NotImplementedError
