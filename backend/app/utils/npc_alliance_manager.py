"""NPC alliance system - player forms alliances with NPCs."""
from typing import Dict, Any, Optional
from app.models.npc import NPCState
from app.models.game_state import GameState
from app.utils.logger import get_logger
import random

logger = get_logger(__name__)


class NPCAllianceManager:
    """Manages alliances between player and NPCs."""

    @staticmethod
    def form_alliance(
        npc: NPCState,
        game_state: GameState,
        alliance_type: str = "mutual_support"
    ) -> Dict[str, Any]:
        """
        Player forms an alliance with an NPC.

        Args:
            npc: NPC to form alliance with
            game_state: Current GameState
            alliance_type: Type of alliance ("mutual_support", "strategic", "loyalty_pact")

        Returns:
            dict: Alliance formation result
        """
        if not npc.alive:
            return {
                "success": False,
                "reason": f"{npc.name} is not available"
            }
        
        if npc.is_in_breakdown:
            return {
                "success": False,
                "reason": f"{npc.name} is in breakdown and cannot form alliances"
            }
        
        # Check if already in alliance
        if "player" in npc.relationships:
            rel = npc.relationships["player"]
            if rel.trust_level >= 75:
                # Already very high trust - consider it an alliance
                return {
                    "success": False,
                    "reason": f"You already have a strong relationship with {npc.name}",
                    "already_allied": True
                }
        
        # Check if NPC is willing to form alliance
        player_trust = 0
        if "player" in npc.relationships:
            player_trust = npc.relationships["player"].trust_level
        
        acceptance_chance = NPCAllianceManager._calculate_alliance_acceptance(
            npc, player_trust, alliance_type, game_state
        )
        
        will_accept = random.random() < acceptance_chance
        
        if not will_accept:
            refusal_reason = NPCAllianceManager._get_alliance_refusal_reason(npc, player_trust)
            return {
                "success": False,
                "reason": refusal_reason,
                "trust_change": -3 if player_trust > 0 else 0
            }
        
        # Form alliance
        if "player" not in npc.relationships:
            from app.models.npc import NPCRelationship
            npc.relationships["player"] = NPCRelationship(target_npc_id="player")
        
        rel = npc.relationships["player"]
        
        # Boost trust significantly
        trust_boost = random.randint(15, 25)
        rel.trust_level = min(100, rel.trust_level + trust_boost)
        
        # Mark alliance in relationship history
        alliance_marker = f"FORMED ALLIANCE ({alliance_type})"
        rel.relationship_history.append(alliance_marker)
        if len(rel.relationship_history) > 10:
            rel.relationship_history = rel.relationship_history[-10:]
        
        # Add alliance flag to NPC (could add alliance field to NPCState)
        # For now, we'll track it via high trust level and history
        
        # Boost morale slightly
        if hasattr(game_state.world, 'crew_morale'):
            game_state.world.crew_morale = min(100, game_state.world.crew_morale + 3)
        
        logger.info(f"[NPCAllianceManager] Alliance formed with {npc.name} ({alliance_type})")
        
        return {
            "success": True,
            "npc_id": npc.id,
            "npc_name": npc.name,
            "alliance_type": alliance_type,
            "trust_boost": trust_boost,
            "new_trust_level": rel.trust_level,
            "morale_boost": 3,
            "message": f"Formed {alliance_type} alliance with {npc.name}"
        }

    @staticmethod
    def check_alliance_status(npc: NPCState) -> Dict[str, Any]:
        """
        Check if player has alliance with NPC.

        Args:
            npc: NPC to check

        Returns:
            dict: Alliance status
        """
        if "player" not in npc.relationships:
            return {
                "has_alliance": False,
                "trust_level": 0,
                "alliance_strength": "none"
            }
        
        rel = npc.relationships["player"]
        trust = rel.trust_level
        
        # Check history for alliance marker
        has_alliance_marker = any("ALLIANCE" in h.upper() for h in rel.relationship_history)
        
        if trust >= 75 or has_alliance_marker:
            if trust >= 90:
                strength = "strong"
            elif trust >= 80:
                strength = "moderate"
            else:
                strength = "weak"
            
            return {
                "has_alliance": True,
                "trust_level": trust,
                "alliance_strength": strength,
                "alliance_type": "mutual_support"  # Default, could be extracted from history
            }
        else:
            return {
                "has_alliance": False,
                "trust_level": trust,
                "alliance_strength": "none"
            }

    @staticmethod
    def _calculate_alliance_acceptance(
        npc: NPCState,
        player_trust: int,
        alliance_type: str,
        game_state: GameState
    ) -> float:
        """Calculate probability NPC will accept alliance."""
        base_chance = 0.3
        
        # Trust requirement
        if player_trust >= 50:
            base_chance += 0.4
        elif player_trust >= 30:
            base_chance += 0.2
        elif player_trust < 10:
            base_chance -= 0.3
        
        # Alliance type modifier
        if alliance_type == "loyalty_pact":
            # Requires very high trust
            if player_trust < 40:
                base_chance -= 0.2
            else:
                base_chance += 0.1
        elif alliance_type == "strategic":
            # More pragmatic, easier to form
            base_chance += 0.1
        
        # Personality modifier
        if hasattr(npc.personality, 'core_value'):
            if npc.personality.core_value in ["loyalty", "duty"]:
                base_chance += 0.15
            elif npc.personality.core_value in ["independence", "survival"]:
                base_chance -= 0.15
        
        # Stress modifier
        if npc.stress_level > 70:
            # High stress - may be more willing to form alliance for support
            base_chance += 0.1
        elif npc.stress_level < 30:
            # Low stress - less need for alliance
            base_chance -= 0.05
        
        # Current morale
        if hasattr(game_state.world, 'crew_morale'):
            if game_state.world.crew_morale < 40:
                # Low morale - more willing to form alliances
                base_chance += 0.1
        
        return max(0.1, min(0.85, base_chance))

    @staticmethod
    def _get_alliance_refusal_reason(npc: NPCState, player_trust: int) -> str:
        """Generate reason for alliance refusal."""
        if player_trust < 30:
            return f"{npc.name} says, 'I don't trust you enough for that kind of commitment.'"
        elif hasattr(npc.personality, 'core_value') and npc.personality.core_value == "independence":
            return f"{npc.name} says, 'I prefer to work independently.'"
        else:
            return f"{npc.name} politely declines: 'I need to think about this more carefully.'"
