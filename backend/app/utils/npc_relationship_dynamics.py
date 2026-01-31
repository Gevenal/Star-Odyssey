"""NPC relationship dynamics - automatic relationship changes."""
from typing import Dict, Any, List
from app.models.npc import NPCState
from app.models.game_state import GameState
from app.utils.logger import get_logger
import random

logger = get_logger(__name__)


class NPCRelationshipDynamics:
    """Manages automatic NPC relationship changes based on interactions and events."""

    @staticmethod
    def update_relationships_from_interactions(game_state: GameState) -> List[Dict[str, Any]]:
        """
        Update NPC relationships based on their interactions and proximity.

        Args:
            game_state: Current GameState

        Returns:
            List[dict]: Relationship changes made
        """
        changes = []
        
        # Group NPCs by location
        location_groups: Dict[str, List[NPCState]] = {}
        for npc in game_state.npcs.values():
            if not npc.alive:
                continue
            if npc.location not in location_groups:
                location_groups[npc.location] = []
            location_groups[npc.location].append(npc)
        
        # Process NPCs at same location (potential for interaction)
        for location, npcs_at_location in location_groups.items():
            if len(npcs_at_location) < 2:
                continue
            
            # Check for NPCs working together or in conflict
            for i, npc1 in enumerate(npcs_at_location):
                for npc2 in npcs_at_location[i + 1:]:
                    # Skip if same NPC
                    if npc1.id == npc2.id:
                        continue
                    
                    # Check if they're working on similar goals
                    shared_goals = set(npc1.goals) & set(npc2.goals)
                    if shared_goals:
                        # Working together - improve relationship
                        change = NPCRelationshipDynamics._improve_relationship(npc1, npc2, "working together on shared goals")
                        if change:
                            changes.append(change)
                    
                    # Check for conflicting goals or stress-induced conflicts
                    if npc1.stress_level > 80 and npc2.stress_level > 80:
                        # Both highly stressed - potential conflict
                        if random.random() < 0.3:  # 30% chance of conflict
                            change = NPCRelationshipDynamics._worsen_relationship(npc1, npc2, "stress-induced conflict")
                            if change:
                                changes.append(change)
                    
                    # Check if one NPC helped another (based on current activity)
                    if npc1.current_activity and "help" in npc1.current_activity.lower():
                        if npc2.id in npc1.current_activity or npc2.name in npc1.current_activity:
                            change = NPCRelationshipDynamics._improve_relationship(npc1, npc2, f"{npc1.name} helped {npc2.name}")
                            if change:
                                changes.append(change)
        
        return changes

    @staticmethod
    def _improve_relationship(npc1: NPCState, npc2: NPCState, reason: str) -> Dict[str, Any]:
        """Improve relationship between two NPCs."""
        from app.models.npc import NPCRelationship
        
        # Ensure relationship exists
        if npc2.id not in npc1.relationships:
            npc1.relationships[npc2.id] = NPCRelationship(
                target_npc_id=npc2.id,
                trust_level=0,
                relationship_history=[]
            )
        
        rel = npc1.relationships[npc2.id]
        old_trust = rel.trust_level
        trust_increase = random.randint(2, 5)
        rel.trust_level = min(100, rel.trust_level + trust_increase)
        rel.relationship_history.append(reason)
        
        # Keep history limited
        if len(rel.relationship_history) > 10:
            rel.relationship_history = rel.relationship_history[-10:]
        
        logger.debug(f"[NPCRelationshipDynamics] {npc1.name} -> {npc2.name}: trust +{trust_increase} ({old_trust} -> {rel.trust_level})")
        
        return {
            "npc1_id": npc1.id,
            "npc2_id": npc2.id,
            "trust_change": trust_increase,
            "reason": reason
        }

    @staticmethod
    def _worsen_relationship(npc1: NPCState, npc2: NPCState, reason: str) -> Dict[str, Any]:
        """Worsen relationship between two NPCs."""
        from app.models.npc import NPCRelationship
        
        # Ensure relationship exists
        if npc2.id not in npc1.relationships:
            npc1.relationships[npc2.id] = NPCRelationship(
                target_npc_id=npc2.id,
                trust_level=0,
                relationship_history=[]
            )
        
        rel = npc1.relationships[npc2.id]
        old_trust = rel.trust_level
        trust_decrease = random.randint(2, 5)
        rel.trust_level = max(-100, rel.trust_level - trust_decrease)
        rel.relationship_history.append(reason)
        
        # Keep history limited
        if len(rel.relationship_history) > 10:
            rel.relationship_history = rel.relationship_history[-10:]
        
        logger.debug(f"[NPCRelationshipDynamics] {npc1.name} -> {npc2.name}: trust -{trust_decrease} ({old_trust} -> {rel.trust_level})")
        
        return {
            "npc1_id": npc1.id,
            "npc2_id": npc2.id,
            "trust_change": -trust_decrease,
            "reason": reason
        }
