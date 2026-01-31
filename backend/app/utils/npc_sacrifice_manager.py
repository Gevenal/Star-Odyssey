"""NPC sacrifice system - NPCs may sacrifice themselves for crew."""
from typing import Dict, Any, Optional
from app.models.npc import NPCState
from app.models.game_state import GameState
from app.utils.logger import get_logger
import random

logger = get_logger(__name__)


class NPCSacrificeManager:
    """Manages NPC sacrifice behavior."""

    @staticmethod
    def check_sacrifice_opportunity(
        npc: NPCState,
        game_state: GameState
    ) -> Optional[Dict[str, Any]]:
        """
        Check if NPC should sacrifice themselves.

        Args:
            npc: NPC to check
            game_state: Current GameState

        Returns:
            dict: Sacrifice opportunity or None
        """
        if not npc.alive:
            return None
        
        # Check for critical situations where sacrifice would help
        sacrifice_opportunities = []
        
        # Critical resource crisis
        if hasattr(game_state.world, 'resources'):
            resources = game_state.world.resources
            oxygen = getattr(resources, 'oxygen_level', {})
            oxygen_val = oxygen.get('current', 100) if isinstance(oxygen, dict) else oxygen
            
            if oxygen_val < 10:
                sacrifice_opportunities.append({
                    "type": "oxygen_crisis",
                    "description": "Oxygen critically low - NPC could perform dangerous EVA repair",
                    "risk": "high",
                    "benefit": "Restore oxygen system"
                })
        
        # Reactor meltdown
        reactor = getattr(resources, 'reactor_level', {}) if hasattr(game_state.world, 'resources') else {}
        reactor_val = reactor.get('current', 100) if isinstance(reactor, dict) else reactor
        if reactor_val < 5:
            sacrifice_opportunities.append({
                "type": "reactor_meltdown",
                "description": "Reactor about to meltdown - NPC could manually override",
                "risk": "fatal",
                "benefit": "Prevent reactor meltdown, save ship"
            })
        
        # Multiple crew members in danger
        critical_npcs = [n for n in game_state.npcs.values() if n.alive and n.health < 20]
        if len(critical_npcs) >= 3:
            sacrifice_opportunities.append({
                "type": "save_crew",
                "description": "Multiple crew members dying - NPC could take extreme risk to save them",
                "risk": "high",
                "benefit": "Save multiple crew members"
            })
        
        if not sacrifice_opportunities:
            return None
        
        # Check if NPC would sacrifice (based on personality and relationships)
        sacrifice_willingness = NPCSacrificeManager._calculate_sacrifice_willingness(npc, game_state)
        
        if sacrifice_willingness < 30:
            return None  # Not willing to sacrifice
        
        # Select most critical opportunity
        opportunity = max(sacrifice_opportunities, key=lambda x: 1 if x["risk"] == "fatal" else 0)
        
        return {
            "opportunity": opportunity,
            "willingness": sacrifice_willingness,
            "npc_id": npc.id,
            "npc_name": npc.name
        }

    @staticmethod
    def _calculate_sacrifice_willingness(
        npc: NPCState,
        game_state: GameState
    ) -> int:
        """Calculate how willing NPC is to sacrifice themselves."""
        willingness = 50  # Base willingness
        
        # Personality factors
        if hasattr(npc.personality, 'core_value'):
            if npc.personality.core_value in ["duty", "selfless", "loyalty"]:
                willingness += 30
            elif npc.personality.core_value in ["survival", "selfish"]:
                willingness -= 20
        
        if hasattr(npc.personality, 'morality'):
            if npc.personality.morality == "selfless":
                willingness += 25
            elif npc.personality.morality == "selfish":
                willingness -= 15
        
        # Relationship with crew
        total_trust = 0
        trust_count = 0
        for other_npc in game_state.npcs.values():
            if other_npc.id == npc.id or not other_npc.alive:
                continue
            rel = npc.relationships.get(other_npc.id)
            if rel:
                total_trust += rel.trust_level
                trust_count += 1
        
        if trust_count > 0:
            avg_trust = total_trust / trust_count
            if avg_trust > 50:
                willingness += 20  # Cares about crew
            elif avg_trust < -20:
                willingness -= 15  # Doesn't care about crew
        
        # Health (dying NPCs more willing)
        if npc.health < 30:
            willingness += 15
        
        return max(0, min(100, willingness))

    @staticmethod
    def execute_sacrifice(
        npc: NPCState,
        game_state: GameState,
        sacrifice_type: str
    ) -> Dict[str, Any]:
        """
        Execute NPC sacrifice.

        Args:
            npc: NPC sacrificing themselves
            game_state: Current GameState
            sacrifice_type: Type of sacrifice

        Returns:
            dict: Sacrifice result
        """
        # NPC dies
        npc.alive = False
        npc.health = 0
        
        sacrifice_event = {
            "npc_id": npc.id,
            "npc_name": npc.name,
            "npc_role": npc.role,
            "turn": game_state.turn_count,
            "type": "sacrifice",
            "sacrifice_type": sacrifice_type
        }
        
        # Apply benefits based on sacrifice type
        benefits = {}
        
        if sacrifice_type == "oxygen_crisis":
            # Restore oxygen
            if hasattr(game_state.world, 'resources'):
                resources = game_state.world.resources
                oxygen = getattr(resources, 'oxygen_level', {})
                if isinstance(oxygen, dict):
                    oxygen["current"] = min(100, oxygen.get("current", 0) + 30)
                    benefits["oxygen_restored"] = 30
                else:
                    # If oxygen is just a number
                    benefits["oxygen_restored"] = 30
        
        elif sacrifice_type == "reactor_meltdown":
            # Prevent meltdown, restore reactor
            if hasattr(game_state.world, 'resources'):
                resources = game_state.world.resources
                reactor = getattr(resources, 'reactor_level', {})
                if isinstance(reactor, dict):
                    reactor["current"] = min(100, reactor.get("current", 0) + 50)
                    benefits["reactor_stabilized"] = True
        
        elif sacrifice_type == "save_crew":
            # Heal multiple crew members
            healed_count = 0
            for other_npc in game_state.npcs.values():
                if other_npc.id != npc.id and other_npc.alive and other_npc.health < 50:
                    other_npc.health = min(100, other_npc.health + 40)
                    healed_count += 1
                    if healed_count >= 3:
                        break
            benefits["crew_healed"] = healed_count
        
        # Impact on morale (heroic sacrifice boosts morale)
        if hasattr(game_state.world, 'crew_morale'):
            game_state.world.crew_morale = min(100, game_state.world.crew_morale + 20)
            benefits["morale_boost"] = 20
        
        # Impact on other NPCs (increase trust with player for heroic act)
        for other_npc in game_state.npcs.values():
            if other_npc.id == npc.id or not other_npc.alive:
                continue
            if "player" in other_npc.relationships:
                rel = other_npc.relationships["player"]
                rel.trust_level = min(100, rel.trust_level + 10)
                rel.relationship_history.append(f"{npc.name} sacrificed themselves for the crew")
                if len(rel.relationship_history) > 10:
                    rel.relationship_history = rel.relationship_history[-10:]
        
        logger.warning(f"[NPCSacrificeManager] {npc.name} sacrificed themselves: {sacrifice_type}")
        
        return {
            "sacrifice_event": sacrifice_event,
            "benefits": benefits,
            "narration": NPCSacrificeManager.generate_sacrifice_narration(npc, sacrifice_type)
        }

    @staticmethod
    def generate_sacrifice_narration(npc: NPCState, sacrifice_type: str) -> str:
        """Generate sacrifice narration."""
        if sacrifice_type == "oxygen_crisis":
            return f"{npc.name} volunteered for the dangerous EVA repair. 'I'll do it,' they said. The last transmission: 'Tell my family...' Then silence. The oxygen system is restored, but {npc.name} is gone."
        elif sacrifice_type == "reactor_meltdown":
            return f"{npc.name} rushed into the reactor room. 'I can stop it!' The manual override required someone to stay inside. The reactor stabilized, but {npc.name} never came out."
        elif sacrifice_type == "save_crew":
            return f"{npc.name} took extreme risks to save the injured crew members. They succeeded, but the effort was too much. 'Save them...' were their last words."
        else:
            return f"{npc.name} made the ultimate sacrifice for the crew. Their heroism will be remembered."
