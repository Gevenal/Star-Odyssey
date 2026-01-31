"""NPC health management."""
from typing import Dict, Any, Optional
from app.models.npc import NPCState
from app.models.game_state import GameState
from app.utils.logger import get_logger

logger = get_logger(__name__)


class NPCHealthManager:
    """Manages NPC health changes and death."""

    @staticmethod
    def apply_health_change(
        npc: NPCState,
        delta: int,
        reason: str = "unknown",
        game_state: Optional[GameState] = None
    ) -> Dict[str, Any]:
        """
        Apply health change to NPC.

        Args:
            npc: NPC to modify
            delta: Health change (positive = heal, negative = damage)
            reason: Reason for health change
            game_state: Optional game state for context

        Returns:
            dict: Result with 'died', 'critical', etc.
        """
        old_health = npc.health
        new_health = max(0, min(100, npc.health + delta))
        npc.health = new_health
        
        result = {
            "old_health": old_health,
            "new_health": new_health,
            "delta": delta,
            "reason": reason,
            "died": False,
            "critical": False
        }
        
        # Check for death
        if new_health <= 0 and npc.alive:
            npc.alive = False
            result["died"] = True
            logger.warning(f"[NPCHealthManager] {npc.name} died: {reason}")
        
        # Check for critical health
        if new_health <= 25 and old_health > 25:
            result["critical"] = True
            logger.info(f"[NPCHealthManager] {npc.name} is in critical condition")
        
        return result

    @staticmethod
    def check_environmental_damage(npc: NPCState, game_state: GameState) -> Optional[Dict[str, Any]]:
        """
        Check if NPC should take environmental damage.

        Args:
            npc: NPC to check
            game_state: Current GameState

        Returns:
            dict: Damage result if damage occurred, None otherwise
        """
        damage = 0
        reason = ""
        
        # Low oxygen damage
        if hasattr(game_state.world, 'resources'):
            resources = game_state.world.resources
            oxygen = getattr(resources, 'oxygen_level', {})
            oxygen_val = oxygen.get('current', 100) if isinstance(oxygen, dict) else oxygen
            
            if oxygen_val < 20:
                damage = 2
                reason = "oxygen_deprivation"
            elif oxygen_val < 40:
                damage = 1
                reason = "low_oxygen"
        
        # Radiation exposure (if applicable)
        # This would need radiation data in world state
        
        if damage > 0:
            return NPCHealthManager.apply_health_change(npc, -damage, reason, game_state)
        
        return None

    @staticmethod
    def heal_npc(
        npc: NPCState,
        amount: int,
        healer_id: Optional[str] = None,
        method: str = "medical_treatment"
    ) -> Dict[str, Any]:
        """
        Heal an NPC.

        Args:
            npc: NPC to heal
            amount: Healing amount
            healer_id: ID of NPC/player doing the healing
            method: Healing method

        Returns:
            dict: Healing result
        """
        if not npc.alive:
            return {"success": False, "reason": "NPC is dead"}
        
        old_health = npc.health
        result = NPCHealthManager.apply_health_change(
            npc, amount, f"healed by {healer_id or 'unknown'}", None
        )
        result["success"] = True
        result["healed_amount"] = min(amount, 100 - old_health)
        
        logger.info(f"[NPCHealthManager] {npc.name} healed {result['healed_amount']} HP by {healer_id or 'unknown'}")
        
        return result
