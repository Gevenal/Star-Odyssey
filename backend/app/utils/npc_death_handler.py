"""NPC death handling and consequences."""
from typing import Dict, Any, List
from app.models.npc import NPCState
from app.models.game_state import GameState
from app.utils.logger import get_logger

logger = get_logger(__name__)


class NPCDeathHandler:
    """Handles NPC death events and consequences."""

    @staticmethod
    def handle_npc_death(
        npc: NPCState,
        game_state: GameState,
        cause: str = "unknown"
    ) -> Dict[str, Any]:
        """
        Handle NPC death and apply consequences.

        Args:
            npc: Dead NPC
            game_state: Current GameState
            cause: Cause of death

        Returns:
            dict: Death event data
        """
        # Generate death event
        death_event = {
            "npc_id": npc.id,
            "npc_name": npc.name,
            "npc_role": npc.role,
            "cause": cause,
            "turn": game_state.turn_count,
            "location": npc.location
        }
        
        # Apply morale/panic impact
        morale_impact = 0
        panic_impact = 0
        
        if hasattr(game_state.world, 'crew_morale'):
            # Death reduces morale
            morale_impact = -15
            game_state.world.crew_morale = max(0, game_state.world.crew_morale + morale_impact)
        
        if hasattr(game_state.world, 'panic_level'):
            # Death increases panic
            panic_impact = 10
            game_state.world.panic_level = min(100, game_state.world.panic_level + panic_impact)
        
        # Impact on other NPCs (increase stress)
        stress_impact = {}
        for other_npc in game_state.npcs.values():
            if other_npc.id == npc.id or not other_npc.alive:
                continue
            
            # Check relationship
            relationship = other_npc.relationships.get(npc.id)
            if relationship:
                trust = relationship.trust_level
                # Higher trust = more stress from death
                stress_increase = max(5, min(20, abs(trust) // 5))
            else:
                # Default stress increase for any crew death
                stress_increase = 10
            
            other_npc.stress_level = min(100, other_npc.stress_level + stress_increase)
            stress_impact[other_npc.id] = stress_increase
            
            # Update breakdown state
            other_npc.update_breakdown_state()
        
        logger.warning(f"[NPCDeathHandler] {npc.name} died: {cause}. Morale: {morale_impact}, Panic: {panic_impact}")
        
        return {
            "death_event": death_event,
            "morale_impact": morale_impact,
            "panic_impact": panic_impact,
            "stress_impact": stress_impact
        }

    @staticmethod
    def generate_death_narration(npc: NPCState, cause: str) -> str:
        """
        Generate death narration.

        Args:
            npc: Dead NPC
            cause: Cause of death

        Returns:
            str: Death narration
        """
        if cause == "oxygen_deprivation" or cause == "low_oxygen":
            return f"{npc.name} collapsed, gasping for air. The oxygen deprivation was too much."
        elif cause == "critical_injury":
            return f"{npc.name} succumbed to their injuries. Medical help came too late."
        elif cause == "system_failure":
            return f"{npc.name} was caught in a system failure. The ship's safety systems failed them."
        else:
            return f"{npc.name} has died. The crew is shaken by the loss."
