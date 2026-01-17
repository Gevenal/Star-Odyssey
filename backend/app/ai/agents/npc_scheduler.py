"""NPC action scheduling and coordination."""
from typing import List, Dict, Any


class NPCScheduler:
    """Manages NPC turn scheduling and action coordination."""

    def __init__(self, npc_repo):
        """
        Initialize NPC scheduler.

        Args:
            npc_repo: NPCRepository instance
        """
        self.npc_repo = npc_repo
        self.npc_agents: Dict[str, Any] = {}

    def register_npc_agent(self, npc_id: str, agent):
        """
        Register an NPC agent.

        Args:
            npc_id: NPC identifier
            agent: NPCAgent instance
        """
        raise NotImplementedError

    async def schedule_npc_turns(self, game_state) -> List[str]:
        """
        Determine which NPCs should act this turn.

        Args:
            game_state: Current GameState

        Returns:
            list[str]: NPC IDs scheduled to act
        """
        raise NotImplementedError

    async def execute_npc_turn(self, npc_id: str, game_state) -> Dict[str, Any]:
        """
        Execute a single NPC's turn.

        Args:
            npc_id: NPC identifier
            game_state: Current GameState

        Returns:
            dict: NPC action results
        """
        raise NotImplementedError

    async def execute_all_npc_turns(self, game_state) -> List[Dict[str, Any]]:
        """
        Execute all scheduled NPC turns.

        Args:
            game_state: Current GameState

        Returns:
            list[dict]: All NPC action results
        """
        raise NotImplementedError
