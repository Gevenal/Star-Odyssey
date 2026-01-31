"""Morale boost system - player actively boosts crew morale."""
from typing import Dict, Any, Optional
from app.models.game_state import GameState
from app.utils.logger import get_logger
import random

logger = get_logger(__name__)


class MoraleBoostManager:
    """Manages player actions to boost crew morale."""

    @staticmethod
    def boost_morale(
        game_state: GameState,
        boost_method: str = "speech",
        target_npcs: Optional[list] = None
    ) -> Dict[str, Any]:
        """
        Player actively boosts crew morale.

        Args:
            game_state: Current GameState
            boost_method: Method of boosting ("speech", "action", "resource_sharing", "celebration")
            target_npcs: Optional list of NPC IDs to target (None = all NPCs)

        Returns:
            dict: Boost result
        """
        if not hasattr(game_state.world, 'crew_morale'):
            return {
                "success": False,
                "reason": "Morale system not available"
            }
        
        initial_morale = game_state.world.crew_morale
        
        # Calculate morale boost
        base_boost = MoraleBoostManager._calculate_morale_boost(
            game_state, boost_method, target_npcs
        )
        
        # Apply boost
        new_morale = min(100, initial_morale + base_boost)
        game_state.world.crew_morale = new_morale
        
        # Update NPC stress (boosting morale reduces stress)
        stress_reduction = base_boost // 2  # Half of morale boost
        affected_npcs = []
        
        npcs_to_affect = target_npcs if target_npcs else list(game_state.npcs.keys())
        for npc_id in npcs_to_affect:
            npc = game_state.npcs.get(npc_id)
            if npc and npc.alive:
                old_stress = npc.stress_level
                npc.stress_level = max(0, npc.stress_level - stress_reduction)
                npc.update_breakdown_state()
                affected_npcs.append({
                    "npc_id": npc_id,
                    "npc_name": npc.name,
                    "stress_reduction": old_stress - npc.stress_level
                })
        
        # Improve player relationships with affected NPCs
        relationship_improvements = {}
        for npc_id in npcs_to_affect:
            npc = game_state.npcs.get(npc_id)
            if npc and npc.alive and "player" in npc.relationships:
                rel = npc.relationships["player"]
                trust_increase = random.randint(2, 5)
                rel.trust_level = min(100, rel.trust_level + trust_increase)
                rel.relationship_history.append(f"Player boosted crew morale ({boost_method})")
                if len(rel.relationship_history) > 10:
                    rel.relationship_history = rel.relationship_history[-10:]
                relationship_improvements[npc_id] = trust_increase
        
        logger.info(f"[MoraleBoostManager] Morale boosted from {initial_morale} to {new_morale} using {boost_method}")
        
        return {
            "success": True,
            "initial_morale": initial_morale,
            "new_morale": new_morale,
            "morale_boost": base_boost,
            "method": boost_method,
            "affected_npcs": affected_npcs,
            "relationship_improvements": relationship_improvements,
            "message": f"Morale boosted from {initial_morale} to {new_morale} using {boost_method}"
        }

    @staticmethod
    def _calculate_morale_boost(
        game_state: GameState,
        method: str,
        target_npcs: Optional[list]
    ) -> int:
        """Calculate morale boost amount."""
        base_boost = 0
        
        # Method-specific boosts
        if method == "speech":
            base_boost = random.randint(5, 10)
        elif method == "action":
            # Heroic action (e.g., saving someone, fixing critical system)
            base_boost = random.randint(10, 15)
        elif method == "resource_sharing":
            # Sharing resources fairly
            base_boost = random.randint(8, 12)
        elif method == "celebration":
            # Small celebration or recognition
            base_boost = random.randint(6, 10)
        else:
            base_boost = random.randint(5, 8)
        
        # Current morale affects boost effectiveness
        current_morale = game_state.world.crew_morale
        if current_morale < 30:
            # Very low morale - boost is more effective
            base_boost = int(base_boost * 1.2)
        elif current_morale > 70:
            # Already high morale - boost is less effective
            base_boost = int(base_boost * 0.8)
        
        # Number of NPCs affected
        if target_npcs:
            # Targeted boost - more effective per NPC
            base_boost = int(base_boost * (1 + len(target_npcs) * 0.1))
        else:
            # All NPCs - base boost
            pass
        
        # Check for recent deaths (affects boost effectiveness)
        recent_deaths = sum(1 for npc in game_state.npcs.values() if not npc.alive)
        if recent_deaths > 0:
            # Recent deaths make morale harder to boost
            base_boost = int(base_boost * (1 - recent_deaths * 0.1))
        
        return max(1, base_boost)
