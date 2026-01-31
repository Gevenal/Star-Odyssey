"""NPC goals dynamic management."""
from typing import List, Dict, Any
from app.models.npc import NPCState
from app.models.game_state import GameState
from app.utils.logger import get_logger

logger = get_logger(__name__)


class NPCGoalsManager:
    """Manages dynamic NPC goal updates based on game state."""

    @staticmethod
    def update_npc_goals(npc: NPCState, game_state: GameState) -> List[str]:
        """
        Update NPC goals based on current game state.

        Args:
            npc: NPC to update goals for
            game_state: Current GameState

        Returns:
            List[str]: Newly added goals
        """
        new_goals = []
        current_goals = set(npc.goals)
        
        # Check resource crisis - add urgent goals
        if hasattr(game_state.world, 'resources'):
            resources = game_state.world.resources
            
            # Oxygen crisis
            oxygen = getattr(resources, 'oxygen_level', {})
            oxygen_val = oxygen.get('current', 100) if isinstance(oxygen, dict) else oxygen
            if oxygen_val < 30 and "emergency_oxygen" not in current_goals:
                if npc.role in ["Engineer", "Chief Engineer", "Ship Captain"]:
                    new_goals.append("emergency_oxygen_repair")
                    logger.info(f"[NPCGoalsManager] Added emergency oxygen goal for {npc.name}")
            
            # Power crisis
            power = getattr(resources, 'power_level', {})
            power_val = power.get('current', 100) if isinstance(power, dict) else power
            if power_val < 25 and "emergency_power" not in current_goals:
                if npc.role in ["Engineer", "Chief Engineer"]:
                    new_goals.append("emergency_power_restoration")
                    logger.info(f"[NPCGoalsManager] Added emergency power goal for {npc.name}")
        
        # Check crew morale/panic
        if hasattr(game_state.world, 'panic_level') and game_state.world.panic_level > 70:
            if "calm_crew" not in current_goals and npc.role in ["Ship Captain", "Chief Medical Officer"]:
                new_goals.append("calm_crew")
                logger.info(f"[NPCGoalsManager] Added calm crew goal for {npc.name}")
        
        # Check for injured NPCs - medical staff should help
        injured_npcs = [n for n in game_state.npcs.values() if n.alive and n.health < 50 and n.id != npc.id]
        if injured_npcs and "treat_injured" not in current_goals:
            if npc.role in ["Medical Officer", "Chief Medical Officer"]:
                new_goals.append("treat_injured")
                logger.info(f"[NPCGoalsManager] Added treat injured goal for {npc.name}")
        
        # Check stress level - add self-care goal
        if npc.stress_level > 80 and "manage_stress" not in current_goals:
            new_goals.append("manage_stress")
            logger.info(f"[NPCGoalsManager] Added manage stress goal for {npc.name}")
        
        # Remove completed goals (simple heuristic)
        completed_goals = []
        for goal in npc.goals:
            if goal.startswith("repair") and "repair" in (npc.current_activity or "").lower():
                # Goal might be in progress, keep it
                continue
            if goal == "manage_stress" and npc.stress_level < 60:
                completed_goals.append(goal)
            if goal == "treat_injured" and not injured_npcs:
                completed_goals.append(goal)
        
        # Update goals
        for goal in completed_goals:
            npc.goals.remove(goal)
            logger.info(f"[NPCGoalsManager] Removed completed goal '{goal}' for {npc.name}")
        
        # Add new goals
        for goal in new_goals:
            if goal not in npc.goals:
                npc.goals.append(goal)
        
        return new_goals
