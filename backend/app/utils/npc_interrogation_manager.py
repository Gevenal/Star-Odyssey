"""NPC interrogation system."""
from typing import Dict, Any, Optional
from app.models.npc import NPCState
from app.models.game_state import GameState
from app.ai.agents.npc_agent import NPCAgent
from app.utils.logger import get_logger

logger = get_logger(__name__)


class NPCInterrogationManager:
    """Manages NPC interrogation (intense questioning)."""

    def __init__(self, gemini_client):
        """
        Initialize interrogation manager.

        Args:
            gemini_client: GeminiClient for AI generation
        """
        self.gemini_client = gemini_client

    async def interrogate_npc(
        self,
        npc: NPCState,
        player_question: str,
        game_state: GameState,
        interrogation_type: str = "questioning"
    ) -> Dict[str, Any]:
        """
        Interrogate an NPC with intense questioning.

        Args:
            npc: NPC being interrogated
            player_question: Player's question
            game_state: Current GameState
            interrogation_type: Type of interrogation ("questioning", "threatening", "confronting")

        Returns:
            dict: Interrogation result
        """
        if not npc.alive:
            return {
                "success": False,
                "response": f"{npc.name} is not available",
                "trust_change": 0
            }
        
        # Build interrogation prompt
        relationship_level = 0
        if "player" in npc.relationships:
            relationship_level = npc.relationships["player"].trust_level
        
        # Get personality info
        from app.ai.prompts.npc_behavior import format_npc_personality
        personality_text = format_npc_personality(npc)
        
        # Interrogation intensity affects response
        intensity_instruction = ""
        trust_penalty = 0
        
        if interrogation_type == "threatening":
            intensity_instruction = "\n⚠️ INTERROGATION: The player is THREATENING you. You feel pressured and may reveal more, but you're also scared or angry."
            trust_penalty = -15
        elif interrogation_type == "confronting":
            intensity_instruction = "\n⚠️ INTERROGATION: The player is CONFRONTING you directly. You feel cornered and may reveal secrets or become defensive."
            trust_penalty = -10
        else:
            intensity_instruction = "\n⚠️ INTERROGATION: The player is QUESTIONING you intensely. You feel pressured to answer truthfully."
            trust_penalty = -5
        
        prompt = f"""You are {npc.name}, the {npc.role} on a damaged spaceship in crisis.

PERSONALITY & BEHAVIOR:
{personality_text}

CURRENT STATE:
- Health: {npc.health}%
- Stress: {npc.stress_level}%
- Trust with Player: {relationship_level}/100
{intensity_instruction}

CONTEXT:
The player is interrogating you. This is an intense questioning session, not a casual conversation.

PLAYER'S QUESTION:
"{player_question}"

INSTRUCTIONS:
1. Respond as {npc.name} would under interrogation pressure
2. Your response should reflect:
   - Your personality (some NPCs break easily, others resist)
   - Your trust level with the player (low trust = less cooperative)
   - Your stress level (high stress = may reveal more or break down)
   - Your secrets (you may accidentally reveal secrets if pressured enough)
3. Under interrogation, you may:
   - Reveal information you normally wouldn't
   - Become defensive or hostile
   - Break down if stress is too high
   - Lie if you have something to hide
4. Keep response concise (2-4 sentences, max 150 words)

Respond now as {npc.name} under interrogation:"""
        
        try:
            response = await self.gemini_client.generate(
                prompt=prompt,
                model="flash",
                temperature=0.9,  # Higher temperature for more varied responses
                max_tokens=200
            )
            
            # Update trust (interrogation reduces trust)
            if "player" in npc.relationships:
                rel = npc.relationships["player"]
                rel.trust_level = max(-100, rel.trust_level + trust_penalty)
                rel.relationship_history.append(f"Interrogated by player ({interrogation_type})")
                if len(rel.relationship_history) > 10:
                    rel.relationship_history = rel.relationship_history[-10:]
            
            # Check for secret revelation (interrogation may force secrets)
            from app.utils.npc_secret_manager import NPCSecretManager
            context = {
                "action_type": "interrogation",
                "interrogation_type": interrogation_type,
                "player_question": player_question
            }
            revealed_secrets = NPCSecretManager.check_and_reveal_secrets(
                npc, game_state, context
            )
            
            logger.info(f"[NPCInterrogationManager] Interrogated {npc.name} ({interrogation_type})")
            
            return {
                "success": True,
                "response": response,
                "trust_change": trust_penalty,
                "interrogation_type": interrogation_type,
                "secrets_revealed": [s.id for s in revealed_secrets] if revealed_secrets else []
            }
            
        except Exception as e:
            logger.error(f"[NPCInterrogationManager] Error interrogating {npc.id}: {e}")
            return {
                "success": False,
                "response": f"{npc.name} refuses to answer.",
                "trust_change": trust_penalty
            }
