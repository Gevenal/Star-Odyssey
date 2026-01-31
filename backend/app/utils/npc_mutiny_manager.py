"""NPC mutiny/rebellion system."""
from typing import Dict, Any, List, Optional
from app.models.npc import NPCState
from app.models.game_state import GameState
from app.utils.logger import get_logger
import random

logger = get_logger(__name__)


class NPCMutinyManager:
    """Manages NPC mutiny and rebellion behavior."""

    @staticmethod
    def check_mutiny_risk(
        npc: NPCState,
        game_state: GameState
    ) -> Dict[str, Any]:
        """
        Check if NPC is at risk of mutiny.

        Args:
            npc: NPC to check
            game_state: Current GameState

        Returns:
            dict: Mutiny risk assessment
        """
        if not npc.alive:
            return {"risk": 0, "will_mutiny": False}
        
        risk_score = 0
        
        # Morale factor
        if hasattr(game_state.world, 'crew_morale'):
            morale = game_state.world.crew_morale
            if morale < 20:
                risk_score += 40
            elif morale < 40:
                risk_score += 25
            elif morale < 60:
                risk_score += 10
        
        # Trust with player
        player_trust = 0
        if "player" in npc.relationships:
            player_trust = npc.relationships["player"].trust_level
        
        if player_trust < -50:
            risk_score += 30
        elif player_trust < -25:
            risk_score += 15
        elif player_trust < 0:
            risk_score += 5
        
        # Stress factor
        if npc.stress_level > 90:
            risk_score += 20
        elif npc.stress_level > 75:
            risk_score += 10
        
        # Health factor (desperate NPCs more likely to mutiny)
        if npc.health < 30:
            risk_score += 15
        
        # Personality factor
        if hasattr(npc.personality, 'core_value'):
            if npc.personality.core_value in ["survival", "independence"]:
                risk_score += 10
            elif npc.personality.core_value in ["duty", "loyalty"]:
                risk_score -= 15
        
        # Hidden agenda factor
        if hasattr(npc, 'hidden_agenda_type') and npc.hidden_agenda_type:
            if npc.hidden_agenda_type == "rebel":
                risk_score += 25
            elif npc.hidden_agenda_type == "loyalist":
                risk_score -= 20
        
        risk_score = max(0, min(100, risk_score))
        
        # Determine if mutiny occurs (threshold: 60)
        will_mutiny = risk_score >= 60
        
        return {
            "risk": risk_score,
            "will_mutiny": will_mutiny,
            "npc_id": npc.id,
            "npc_name": npc.name
        }

    @staticmethod
    def trigger_mutiny(
        npc: NPCState,
        game_state: GameState
    ) -> Dict[str, Any]:
        """
        Trigger NPC mutiny.

        Args:
            npc: NPC who is mutinying
            game_state: Current GameState

        Returns:
            dict: Mutiny event data
        """
        mutiny_event = {
            "npc_id": npc.id,
            "npc_name": npc.name,
            "npc_role": npc.role,
            "turn": game_state.turn_count,
            "location": npc.location,
            "type": "mutiny"
        }
        
        # Reduce trust with player significantly
        if "player" not in npc.relationships:
            from app.models.npc import NPCRelationship
            npc.relationships["player"] = NPCRelationship(
                target_npc_id="player",
                trust_level=0,
                relationship_history=[]
            )
        
        rel = npc.relationships["player"]
        rel.trust_level = max(-100, rel.trust_level - 50)
        rel.relationship_history.append(f"{npc.name} mutinied against player command")
        if len(rel.relationship_history) > 10:
            rel.relationship_history = rel.relationship_history[-10:]
        
        # NPC may refuse to follow orders
        npc.current_activity = "refusing orders"
        
        # Impact on morale
        if hasattr(game_state.world, 'crew_morale'):
            game_state.world.crew_morale = max(0, game_state.world.crew_morale - 10)
        
        # Other NPCs may join (based on relationships)
        mutiny_followers = []
        for other_npc in game_state.npcs.values():
            if other_npc.id == npc.id or not other_npc.alive:
                continue
            
            # Check relationship with mutiny leader
            relationship = other_npc.relationships.get(npc.id)
            if relationship and relationship.trust_level > 50:
                # High trust with mutiny leader - may join
                if random.random() < 0.3:  # 30% chance
                    mutiny_followers.append(other_npc.id)
                    # Reduce their trust with player
                    if "player" in other_npc.relationships:
                        other_npc.relationships["player"].trust_level = max(
                            -100, other_npc.relationships["player"].trust_level - 20
                        )
        
        logger.warning(f"[NPCMutinyManager] {npc.name} mutinied! Followers: {mutiny_followers}")
        
        return {
            "mutiny_event": mutiny_event,
            "followers": mutiny_followers,
            "morale_impact": -10
        }

    @staticmethod
    def generate_mutiny_narration(npc: NPCState) -> str:
        """Generate mutiny narration."""
        return f"{npc.name} has openly defied your command. 'I'm not following your orders anymore,' they declare. The crew watches nervously."
