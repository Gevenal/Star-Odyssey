"""NPC task assignment system - player assigns tasks to NPCs."""
from typing import Dict, Any, Optional
from app.models.npc import NPCState
from app.models.game_state import GameState
from app.utils.logger import get_logger

logger = get_logger(__name__)


class NPCTaskAssignment:
    """Manages player-assigned tasks to NPCs."""

    @staticmethod
    def assign_task_to_npc(
        npc: NPCState,
        task_description: str,
        task_type: str,
        game_state: GameState,
        player_trust_level: int
    ) -> Dict[str, Any]:
        """
        Assign a task to an NPC.

        Args:
            npc: NPC to assign task to
            task_description: Description of the task
            task_type: Type of task (e.g., "repair", "medical", "investigation", "security")
            game_state: Current GameState
            player_trust_level: Player's trust level with this NPC

        Returns:
            dict: Assignment result
        """
        if not npc.alive:
            return {
                "success": False,
                "reason": f"{npc.name} is not available"
            }
        
        if npc.is_in_breakdown:
            return {
                "success": False,
                "reason": f"{npc.name} is in breakdown and cannot accept tasks"
            }
        
        # Check if NPC is willing to accept task
        acceptance_chance = NPCTaskAssignment._calculate_acceptance_chance(
            npc, task_type, player_trust_level, game_state
        )
        
        import random
        will_accept = random.random() < acceptance_chance
        
        if not will_accept:
            # NPC refuses
            refusal_reason = NPCTaskAssignment._get_refusal_reason(npc, task_type, player_trust_level)
            return {
                "success": False,
                "reason": refusal_reason,
                "trust_change": -5 if player_trust_level > 0 else 0
            }
        
        # NPC accepts task
        # Add task to NPC's goals
        task_goal = f"Player assigned: {task_description}"
        if task_goal not in npc.goals:
            npc.goals.insert(0, task_goal)  # Add to front (priority)
        
        # Update current activity
        npc.current_activity = f"Working on assigned task: {task_description}"
        
        # Update relationship (accepting task increases trust slightly)
        trust_change = 3 if player_trust_level >= 0 else 5  # More trust if relationship was negative
        if "player" in npc.relationships:
            rel = npc.relationships["player"]
            rel.trust_level = min(100, rel.trust_level + trust_change)
            rel.relationship_history.append(f"Accepted assigned task: {task_description}")
            if len(rel.relationship_history) > 10:
                rel.relationship_history = rel.relationship_history[-10:]
        
        logger.info(f"[NPCTaskAssignment] {npc.name} accepted task: {task_description}")
        
        return {
            "success": True,
            "npc_id": npc.id,
            "npc_name": npc.name,
            "task_description": task_description,
            "task_type": task_type,
            "trust_change": trust_change,
            "message": f"{npc.name} accepted the task: {task_description}"
        }

    @staticmethod
    def _calculate_acceptance_chance(
        npc: NPCState,
        task_type: str,
        player_trust: int,
        game_state: GameState
    ) -> float:
        """Calculate probability NPC will accept task."""
        base_chance = 0.5
        
        # Trust modifier
        if player_trust >= 50:
            base_chance += 0.3
        elif player_trust >= 25:
            base_chance += 0.15
        elif player_trust < 0:
            base_chance -= 0.2
        
        # Role compatibility
        role = npc.role.lower()
        task_lower = task_type.lower()
        
        if "medical" in task_lower and ("medical" in role or "doctor" in role):
            base_chance += 0.2
        elif "repair" in task_lower and ("engineer" in role or "maintenance" in role):
            base_chance += 0.2
        elif "security" in task_lower and "security" in role:
            base_chance += 0.2
        elif "investigation" in task_lower and ("scientist" in role or "research" in role):
            base_chance += 0.2
        else:
            # Task doesn't match role - lower chance
            base_chance -= 0.1
        
        # Stress modifier (stressed NPCs less likely to accept)
        if npc.stress_level > 70:
            base_chance -= 0.15
        elif npc.stress_level > 50:
            base_chance -= 0.05
        
        # Personality modifier
        if hasattr(npc.personality, 'core_value'):
            if npc.personality.core_value in ["duty", "loyalty"]:
                base_chance += 0.1
            elif npc.personality.core_value in ["independence", "survival"]:
                base_chance -= 0.1
        
        return max(0.1, min(0.95, base_chance))

    @staticmethod
    def _get_refusal_reason(
        npc: NPCState,
        task_type: str,
        player_trust: int
    ) -> str:
        """Generate reason for task refusal."""
        if player_trust < 0:
            return f"{npc.name} doesn't trust you enough to accept this task."
        elif npc.stress_level > 70:
            return f"{npc.name} is too stressed to take on additional tasks right now."
        else:
            role = npc.role.lower()
            task_lower = task_type.lower()
            if "medical" not in task_lower and ("medical" in role or "doctor" in role):
                return f"{npc.name} says, 'That's not my area of expertise.'"
            elif "repair" not in task_lower and ("engineer" in role or "maintenance" in role):
                return f"{npc.name} says, 'I'm not qualified for that.'"
            else:
                return f"{npc.name} politely declines: 'I have other priorities right now.'"
