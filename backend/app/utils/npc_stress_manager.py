"""NPC stress management and automatic increase."""
from typing import Dict, Any
from app.models.npc import NPCState
from app.models.game_state import GameState
from app.utils.logger import get_logger

logger = get_logger(__name__)


class NPCStressManager:
    """Manages automatic NPC stress changes based on game state."""

    @staticmethod
    def calculate_stress_increase(npc: NPCState, game_state: GameState) -> int:
        """
        Calculate stress increase for NPC based on game conditions.

        Args:
            npc: NPC to calculate stress for
            game_state: Current GameState

        Returns:
            int: Stress increase amount (0-10)
        """
        stress_increase = 0
        
        # Base stress from crisis (everyone feels it)
        if hasattr(game_state.world, 'panic_level'):
            panic = game_state.world.panic_level
            if panic > 80:
                stress_increase += 3
            elif panic > 60:
                stress_increase += 2
            elif panic > 40:
                stress_increase += 1
        
        # Resource crisis stress
        if hasattr(game_state.world, 'resources'):
            resources = game_state.world.resources
            
            # Low oxygen stress
            oxygen = getattr(resources, 'oxygen_level', {})
            oxygen_val = oxygen.get('current', 100) if isinstance(oxygen, dict) else oxygen
            if oxygen_val < 20:
                stress_increase += 3
            elif oxygen_val < 40:
                stress_increase += 2
            elif oxygen_val < 60:
                stress_increase += 1
            
            # Low power stress
            power = getattr(resources, 'power_level', {})
            power_val = power.get('current', 100) if isinstance(power, dict) else power
            if power_val < 20:
                stress_increase += 2
            elif power_val < 40:
                stress_increase += 1
        
        # Health-based stress (injured NPCs are more stressed)
        if npc.health < 30:
            stress_increase += 2
        elif npc.health < 50:
            stress_increase += 1
        
        # Death of crew members (already handled in death handler, but add base stress)
        alive_count = sum(1 for n in game_state.npcs.values() if n.alive)
        total_npcs = len(game_state.npcs)
        if alive_count < total_npcs:
            deaths = total_npcs - alive_count
            stress_increase += min(2, deaths)  # Max 2 stress per turn from deaths
        
        # Personality-based stress modifiers
        if hasattr(npc.personality, 'stress_response'):
            if npc.personality.stress_response == "freezes":
                # Freezers get more stressed
                stress_increase = int(stress_increase * 1.2)
            elif npc.personality.stress_response == "proactive":
                # Proactive NPCs handle stress better
                stress_increase = int(stress_increase * 0.8)
        
        # Clamp to reasonable range
        stress_increase = min(10, max(0, stress_increase))
        
        return stress_increase

    @staticmethod
    def apply_stress_increase(npc: NPCState, game_state: GameState) -> Dict[str, Any]:
        """
        Apply automatic stress increase to NPC.

        Args:
            npc: NPC to update
            game_state: Current GameState

        Returns:
            dict: Stress change result
        """
        if not npc.alive:
            return {"stress_increase": 0, "new_stress": npc.stress_level, "entered_breakdown": False}
        
        old_stress = npc.stress_level
        was_in_breakdown = npc.is_in_breakdown
        
        # Calculate and apply stress increase
        stress_delta = NPCStressManager.calculate_stress_increase(npc, game_state)
        npc.stress_level = min(100, npc.stress_level + stress_delta)
        
        # Update breakdown state
        npc.update_breakdown_state()
        entered_breakdown = npc.is_in_breakdown and not was_in_breakdown
        
        if stress_delta > 0:
            logger.debug(f"[NPCStressManager] {npc.name} stress increased by {stress_delta} (now {npc.stress_level}%)")
        
        if entered_breakdown:
            logger.warning(f"[NPCStressManager] {npc.name} entered breakdown state!")
        
        return {
            "stress_increase": stress_delta,
            "old_stress": old_stress,
            "new_stress": npc.stress_level,
            "entered_breakdown": entered_breakdown
        }
