"""NPC conflict mediation system - player mediates conflicts between NPCs."""
from typing import Dict, Any, Optional, List
from app.models.npc import NPCState
from app.models.game_state import GameState
from app.utils.logger import get_logger
import random

logger = get_logger(__name__)


class NPCConflictMediation:
    """Manages player mediation of NPC conflicts."""

    @staticmethod
    def find_active_conflicts(game_state: GameState) -> List[Dict[str, Any]]:
        """
        Find active conflicts between NPCs.

        Args:
            game_state: Current GameState

        Returns:
            List of conflict information
        """
        conflicts = []
        npcs_list = list(game_state.npcs.values())
        
        for i, npc1 in enumerate(npcs_list):
            if not npc1.alive:
                continue
            for npc2 in npcs_list[i + 1:]:
                if not npc2.alive:
                    continue
                
                # Check if they're in conflict
                rel1_to_2 = npc1.relationships.get(npc2.id)
                rel2_to_1 = npc2.relationships.get(npc1.id)
                
                # Conflict indicators:
                # 1. Low trust (< -25)
                # 2. Both highly stressed (> 70)
                # 3. Same location (potential for confrontation)
                # 4. Conflicting goals
                
                trust1_to_2 = rel1_to_2.trust_level if rel1_to_2 else 0
                trust2_to_1 = rel2_to_1.trust_level if rel2_to_1 else 0
                avg_trust = (trust1_to_2 + trust2_to_1) / 2
                
                is_conflict = False
                conflict_severity = 0
                
                if avg_trust < -25:
                    is_conflict = True
                    conflict_severity += 2
                
                if npc1.location == npc2.location:
                    conflict_severity += 1
                
                if npc1.stress_level > 70 and npc2.stress_level > 70:
                    conflict_severity += 1
                
                # Check for conflicting goals
                npc1_goals = set(npc1.goals)
                npc2_goals = set(npc2.goals)
                conflicting_keywords = ["sacrifice", "evacuate", "abandon", "prioritize"]
                for keyword in conflicting_keywords:
                    if any(keyword in g.lower() for g in npc1_goals) and any(keyword in g.lower() for g in npc2_goals):
                        conflict_severity += 1
                        break
                
                if is_conflict or conflict_severity >= 2:
                    conflicts.append({
                        "npc1_id": npc1.id,
                        "npc1_name": npc1.name,
                        "npc2_id": npc2.id,
                        "npc2_name": npc2.name,
                        "location": npc1.location if npc1.location == npc2.location else "different_locations",
                        "severity": conflict_severity,
                        "trust_level_npc1_to_npc2": trust1_to_2,
                        "trust_level_npc2_to_npc1": trust2_to_1,
                        "description": NPCConflictMediation._generate_conflict_description(npc1, npc2, conflict_severity)
                    })
        
        return conflicts

    @staticmethod
    def _generate_conflict_description(npc1: NPCState, npc2: NPCState, severity: int) -> str:
        """Generate description of conflict."""
        if severity >= 3:
            return f"Intense conflict between {npc1.name} and {npc2.name}. They are openly hostile."
        elif severity >= 2:
            return f"Tension between {npc1.name} and {npc2.name}. They disagree on priorities."
        else:
            return f"Minor disagreement between {npc1.name} and {npc2.name}."

    @staticmethod
    def mediate_conflict(
        npc1: NPCState,
        npc2: NPCState,
        game_state: GameState,
        mediation_approach: str = "diplomatic"
    ) -> Dict[str, Any]:
        """
        Player mediates conflict between two NPCs.

        Args:
            npc1: First NPC in conflict
            npc2: Second NPC in conflict
            game_state: Current GameState
            mediation_approach: Approach to mediation ("diplomatic", "authoritative", "compromise")

        Returns:
            dict: Mediation result
        """
        if not npc1.alive or not npc2.alive:
            return {
                "success": False,
                "reason": "One or both NPCs are not available"
            }
        
        # Check player trust with both NPCs
        player_trust_npc1 = 0
        player_trust_npc2 = 0
        if "player" in npc1.relationships:
            player_trust_npc1 = npc1.relationships["player"].trust_level
        if "player" in npc2.relationships:
            player_trust_npc2 = npc2.relationships["player"].trust_level
        
        # Calculate mediation success chance
        success_chance = NPCConflictMediation._calculate_mediation_success(
            npc1, npc2, player_trust_npc1, player_trust_npc2, mediation_approach, game_state
        )
        
        success = random.random() < success_chance
        
        if success:
            # Mediation successful
            trust_improvement = random.randint(5, 15)
            
            # Improve relationship between NPCs
            if npc2.id not in npc1.relationships:
                from app.models.npc import NPCRelationship
                npc1.relationships[npc2.id] = NPCRelationship(target_npc_id=npc2.id)
            if npc1.id not in npc2.relationships:
                from app.models.npc import NPCRelationship
                npc2.relationships[npc1.id] = NPCRelationship(target_npc_id=npc1.id)
            
            rel1_to_2 = npc1.relationships[npc2.id]
            rel2_to_1 = npc2.relationships[npc1.id]
            
            rel1_to_2.trust_level = min(100, rel1_to_2.trust_level + trust_improvement)
            rel2_to_1.trust_level = min(100, rel2_to_1.trust_level + trust_improvement)
            
            rel1_to_2.relationship_history.append(f"Conflict mediated by player ({mediation_approach})")
            rel2_to_1.relationship_history.append(f"Conflict mediated by player ({mediation_approach})")
            
            if len(rel1_to_2.relationship_history) > 10:
                rel1_to_2.relationship_history = rel1_to_2.relationship_history[-10:]
            if len(rel2_to_1.relationship_history) > 10:
                rel2_to_1.relationship_history = rel2_to_1.relationship_history[-10:]
            
            # Improve player trust with both NPCs
            if "player" in npc1.relationships:
                npc1.relationships["player"].trust_level = min(100, npc1.relationships["player"].trust_level + 5)
            if "player" in npc2.relationships:
                npc2.relationships["player"].trust_level = min(100, npc2.relationships["player"].trust_level + 5)
            
            # Boost morale
            if hasattr(game_state.world, 'crew_morale'):
                game_state.world.crew_morale = min(100, game_state.world.crew_morale + 5)
            
            logger.info(f"[NPCConflictMediation] Successfully mediated conflict between {npc1.name} and {npc2.name}")
            
            return {
                "success": True,
                "npc1_id": npc1.id,
                "npc2_id": npc2.id,
                "trust_improvement": trust_improvement,
                "morale_boost": 5,
                "message": f"Successfully mediated conflict between {npc1.name} and {npc2.name}"
            }
        else:
            # Mediation failed
            trust_loss = random.randint(2, 8)
            
            # May worsen relationship if mediation backfires
            if random.random() < 0.3:  # 30% chance
                if npc2.id in npc1.relationships:
                    npc1.relationships[npc2.id].trust_level = max(-100, npc1.relationships[npc2.id].trust_level - trust_loss)
                if npc1.id in npc2.relationships:
                    npc2.relationships[npc1.id].trust_level = max(-100, npc2.relationships[npc1.id].trust_level - trust_loss)
            
            logger.warning(f"[NPCConflictMediation] Failed to mediate conflict between {npc1.name} and {npc2.name}")
            
            return {
                "success": False,
                "reason": "Mediation attempt failed. The conflict may have worsened.",
                "trust_loss": trust_loss if random.random() < 0.3 else 0
            }

    @staticmethod
    def _calculate_mediation_success(
        npc1: NPCState,
        npc2: NPCState,
        player_trust1: int,
        player_trust2: int,
        approach: str,
        game_state: GameState
    ) -> float:
        """Calculate probability of successful mediation."""
        base_chance = 0.4
        
        # Average player trust
        avg_player_trust = (player_trust1 + player_trust2) / 2
        if avg_player_trust >= 50:
            base_chance += 0.3
        elif avg_player_trust >= 25:
            base_chance += 0.15
        elif avg_player_trust < 0:
            base_chance -= 0.2
        
        # Approach modifier
        if approach == "authoritative":
            # Works better if player has high trust
            if avg_player_trust >= 50:
                base_chance += 0.1
            else:
                base_chance -= 0.1
        elif approach == "compromise":
            # Works better for moderate conflicts
            base_chance += 0.1
        elif approach == "diplomatic":
            # Balanced approach
            base_chance += 0.05
        
        # NPC personality compatibility
        if hasattr(npc1.personality, 'social_style') and hasattr(npc2.personality, 'social_style'):
            if npc1.personality.social_style == "mediator" or npc2.personality.social_style == "mediator":
                base_chance += 0.1
            if npc1.personality.social_style == "aggressive" and npc2.personality.social_style == "aggressive":
                base_chance -= 0.15
        
        # Stress levels (high stress = harder to mediate)
        avg_stress = (npc1.stress_level + npc2.stress_level) / 2
        if avg_stress > 80:
            base_chance -= 0.2
        elif avg_stress > 60:
            base_chance -= 0.1
        
        return max(0.1, min(0.9, base_chance))
