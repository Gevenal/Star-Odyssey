"""NPC quest/request management."""
from typing import Dict, Any, List, Optional
from app.models.npc import NPCState
from app.models.npc_quest import NPCQuest
from app.models.game_state import GameState
from app.utils.logger import get_logger
import random

logger = get_logger(__name__)


class NPCQuestManager:
    """Manages NPC quests and requests."""

    @staticmethod
    def generate_quest(
        npc: NPCState,
        game_state: GameState,
        quest_type: Optional[str] = None
    ) -> Optional[NPCQuest]:
        """
        Generate a quest from NPC based on game state.

        Args:
            npc: NPC giving the quest
            game_state: Current GameState
            quest_type: Optional quest type hint

        Returns:
            NPCQuest or None if no quest should be given
        """
        # Check if NPC should give a quest
        # Only give quests if:
        # - NPC trusts player enough (trust > 20)
        # - NPC is not in breakdown
        # - NPC has relevant goals
        
        if npc.is_in_breakdown:
            return None
        
        player_trust = 0
        if "player" in npc.relationships:
            player_trust = npc.relationships["player"].trust_level
        
        if player_trust < 20:
            return None  # Not enough trust
        
        # Check if NPC already has active quests for player
        active_quests = [q for q in game_state.player.active_quests if q.startswith(f"quest_{npc.id}")]
        if len(active_quests) >= 2:
            return None  # Too many active quests
        
        # Generate quest based on NPC role and game state
        quest = None
        
        if npc.role in ["Ship Captain", "Captain"]:
            # Captain gives strategic quests
            if hasattr(game_state.world, 'resources'):
                resources = game_state.world.resources
                reactor = getattr(resources, 'reactor_level', {})
                reactor_val = reactor.get('current', 100) if isinstance(reactor, dict) else reactor
                
                if reactor_val < 50:
                    quest = NPCQuest(
                        quest_id=f"quest_{npc.id}_repair_reactor_{game_state.turn_count}",
                        npc_id=npc.id,
                        title="Repair the Reactor",
                        description="The reactor is critical. We need it fixed immediately or we'll lose power completely.",
                        objective="Repair reactor to at least 60%",
                        reward=f"+25 trust with {npc.name}, access to bridge controls",
                        status="active",
                        created_at_turn=game_state.turn_count,
                        conditions={"resource_reactor_level": 60}
                    )
        
        elif npc.role in ["Chief Engineer", "Engineer"]:
            # Engineer gives repair quests
            if hasattr(game_state.world, 'resources'):
                resources = game_state.world.resources
                power = getattr(resources, 'power_level', {})
                power_val = power.get('current', 100) if isinstance(power, dict) else power
                
                if power_val < 40:
                    quest = NPCQuest(
                        quest_id=f"quest_{npc.id}_restore_power_{game_state.turn_count}",
                        npc_id=npc.id,
                        title="Restore Power Systems",
                        description="Power is critically low. I need help restoring the backup generators.",
                        objective="Restore power to at least 50%",
                        reward=f"+20 trust with {npc.name}, technical assistance",
                        status="active",
                        created_at_turn=game_state.turn_count,
                        conditions={"resource_power_level": 50}
                    )
        
        elif npc.role in ["Chief Medical Officer", "Medical Officer"]:
            # Medical officer gives health-related quests
            injured_npcs = [n for n in game_state.npcs.values() if n.alive and n.health < 50]
            if injured_npcs:
                quest = NPCQuest(
                    quest_id=f"quest_{npc.id}_treat_injured_{game_state.turn_count}",
                    npc_id=npc.id,
                    title="Help Treat Injured Crew",
                    description="Several crew members are injured. I need help treating them.",
                    objective="Help treat at least 2 injured crew members",
                    reward=f"+15 trust with {npc.name}, medical supplies",
                    status="active",
                    created_at_turn=game_state.turn_count,
                    conditions={"injured_crew_treated": 2}
                )
        
        if quest:
            logger.info(f"[NPCQuestManager] {npc.name} gave quest: {quest.title}")
        
        return quest

    @staticmethod
    def check_quest_completion(
        quest: NPCQuest,
        game_state: GameState
    ) -> bool:
        """
        Check if quest conditions are met.

        Args:
            quest: Quest to check
            game_state: Current GameState

        Returns:
            bool: True if quest is completed
        """
        if quest.status != "active":
            return False
        
        # Check conditions
        for condition_key, condition_value in quest.conditions.items():
            if condition_key.startswith("resource_"):
                # Resource condition
                resource_name = condition_key.replace("resource_", "").replace("_level", "")
                if hasattr(game_state.world, 'resources'):
                    resources = game_state.world.resources
                    resource = getattr(resources, resource_name, {})
                    resource_val = resource.get('current', 0) if isinstance(resource, dict) else resource
                    if resource_val < condition_value:
                        return False
            elif condition_key == "injured_crew_treated":
                # Count treated NPCs (simplified - would need tracking)
                # For now, check if health improved
                pass
            elif condition_key.startswith("secret_revealed"):
                # Secret condition
                secret_id = condition_value
                if secret_id not in game_state.player.discovered_secrets:
                    return False
        
        return True

    @staticmethod
    def complete_quest(
        quest: NPCQuest,
        game_state: GameState
    ) -> Dict[str, Any]:
        """
        Complete a quest and apply rewards.

        Args:
            quest: Quest to complete
            game_state: Current GameState

        Returns:
            dict: Completion result with rewards
        """
        quest.status = "completed"
        quest.completed_at_turn = game_state.turn_count
        
        # Remove from active, add to completed
        if quest.quest_id in game_state.player.active_quests:
            game_state.player.active_quests.remove(quest.quest_id)
        if quest.quest_id not in game_state.player.completed_quests:
            game_state.player.completed_quests.append(quest.quest_id)
        
        # Apply reward (trust increase)
        npc = game_state.npcs.get(quest.npc_id)
        if npc and "player" in npc.relationships:
            # Parse reward for trust increase
            if "+" in quest.reward and "trust" in quest.reward.lower():
                # Extract trust value
                import re
                match = re.search(r'\+(\d+).*trust', quest.reward.lower())
                if match:
                    trust_increase = int(match.group(1))
                    rel = npc.relationships["player"]
                    rel.trust_level = min(100, rel.trust_level + trust_increase)
                    rel.relationship_history.append(f"Completed quest: {quest.title}")
                    if len(rel.relationship_history) > 10:
                        rel.relationship_history = rel.relationship_history[-10:]
        
        logger.info(f"[NPCQuestManager] Quest completed: {quest.title}")
        
        return {
            "quest_id": quest.quest_id,
            "completed": True,
            "reward": quest.reward
        }
