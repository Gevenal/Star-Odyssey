"""NPC-to-NPC interaction management."""
from typing import Dict, Any, List, Optional
from app.models.npc import NPCState
from app.models.game_state import GameState
from app.ai.agents.npc_agent import NPCAgent
from app.utils.logger import get_logger

logger = get_logger(__name__)


class NPCInteractionManager:
    """Manages interactions between NPCs."""

    def __init__(self, gemini_client):
        """
        Initialize NPC interaction manager.

        Args:
            gemini_client: GeminiClient for AI generation
        """
        self.gemini_client = gemini_client

    async def npc_help_npc(
        self,
        helper: NPCState,
        target: NPCState,
        game_state: GameState,
        help_type: str = "medical"
    ) -> Dict[str, Any]:
        """
        One NPC helps another NPC.

        Args:
            helper: NPC providing help
            target: NPC receiving help
            game_state: Current GameState
            help_type: Type of help ("medical", "repair", "emotional")

        Returns:
            dict: Help result
        """
        if not helper.alive or not target.alive:
            return {"success": False, "reason": "One or both NPCs are dead"}
        
        if helper.location != target.location:
            return {"success": False, "reason": "NPCs are not in same location"}
        
        result = {
            "helper_id": helper.id,
            "helper_name": helper.name,
            "target_id": target.id,
            "target_name": target.name,
            "help_type": help_type,
            "success": True
        }
        
        if help_type == "medical" and helper.role in ["Medical Officer", "Chief Medical Officer"]:
            # Medical help - restore health
            from app.utils.npc_health_manager import NPCHealthManager
            heal_result = NPCHealthManager.heal_npc(target, 15, helper.id, "medical_treatment")
            result["heal_result"] = heal_result
            result["description"] = f"{helper.name} treated {target.name}'s injuries"
        
        elif help_type == "emotional":
            # Emotional support - reduce stress
            stress_reduction = 10
            target.stress_level = max(0, target.stress_level - stress_reduction)
            result["stress_reduction"] = stress_reduction
            result["description"] = f"{helper.name} provided emotional support to {target.name}"
        
        # Update relationship (helper gains trust from target)
        if target.id not in helper.relationships:
            from app.models.npc import NPCRelationship
            helper.relationships[target.id] = NPCRelationship(
                target_npc_id=target.id,
                trust_level=0,
                relationship_history=[]
            )
        
        rel = helper.relationships[target.id]
        rel.trust_level = min(100, rel.trust_level + 5)
        rel.relationship_history.append(f"{helper.name} helped {target.name} ({help_type})")
        if len(rel.relationship_history) > 10:
            rel.relationship_history = rel.relationship_history[-10:]
        
        logger.info(f"[NPCInteractionManager] {helper.name} helped {target.name} ({help_type})")
        
        return result

    async def generate_npc_to_npc_dialogue(
        self,
        npc1: NPCState,
        npc2: NPCState,
        game_state: GameState,
        context: Optional[str] = None
    ) -> str:
        """
        Generate dialogue between two NPCs.

        Args:
            npc1: First NPC
            npc2: Second NPC
            game_state: Current GameState
            context: Optional context for dialogue

        Returns:
            str: Generated dialogue
        """
        if npc1.location != npc2.location:
            return ""
        
        # Get relationship
        relationship = npc1.relationships.get(npc2.id)
        trust_level = relationship.trust_level if relationship else 0
        
        # Build prompt
        prompt = f"""Generate a brief dialogue between two NPCs on a spaceship in crisis.

NPC 1: {npc1.name} ({npc1.role})
- Personality: {npc1.personality.core_value if hasattr(npc1.personality, 'core_value') else 'unknown'}
- Stress: {npc1.stress_level}%
- Health: {npc1.health}%

NPC 2: {npc2.name} ({npc2.role})
- Personality: {npc2.personality.core_value if hasattr(npc2.personality, 'core_value') else 'unknown'}
- Stress: {npc2.stress_level}%
- Health: {npc2.health}%

Relationship: Trust level {trust_level} (-100 to 100)
Context: {context or "General conversation during crisis"}

Generate a brief, natural dialogue (2-3 exchanges) between these NPCs. Keep it concise and in-character.

Format:
{npc1.name}: [dialogue]
{npc2.name}: [dialogue]
{npc1.name}: [dialogue]
"""
        
        try:
            response = await self.gemini_client.generate(
                prompt=prompt,
                model="flash",
                temperature=0.8,
                max_tokens=150
            )
            return response
        except Exception as e:
            logger.error(f"[NPCInteractionManager] Error generating NPC dialogue: {e}")
            return f"{npc1.name} and {npc2.name} exchange a few words."
