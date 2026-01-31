"""NPC AI agent."""
from typing import Any, Dict, Optional
from app.ai.agents.base_agent import BaseAgent
from app.models.game_state import GameState
from app.models.npc import NPCState
from app.ai.prompts.npc_behavior import (
    build_npc_dialogue_prompt,
    build_npc_prompt,
    format_npc_personality
)
from app.utils.logger import get_logger
import json

logger = get_logger(__name__)


class NPCAgent(BaseAgent):
    """AI agent for individual NPC behavior."""

    def __init__(self, gemini_client, npc_id: str):
        """
        Initialize NPC agent.

        Args:
            gemini_client: GeminiClient instance
            npc_id: NPC identifier
        """
        super().__init__(gemini_client)
        self.npc_id = npc_id

    def _get_npc(self, game_state: GameState) -> Optional[NPCState]:
        """Get NPC from game state."""
        return game_state.npcs.get(self.npc_id)

    def can_act(self, game_state: GameState, context: Dict[str, Any] = None) -> bool:
        """
        Check if NPC can act.

        Args:
            game_state: Current GameState
            context: Optional action context

        Returns:
            bool: True if NPC can act
        """
        npc = self._get_npc(game_state)
        if not npc:
            return False
        
        # NPC must be alive
        if not npc.alive:
            return False
        
        # If in breakdown state, check breakdown behavior
        if npc.is_in_breakdown:
            # Some breakdown behaviors prevent action
            if npc.breakdown_behavior:
                breakdown_lower = npc.breakdown_behavior.lower()
                if "refuse" in breakdown_lower or "lock" in breakdown_lower or "isolate" in breakdown_lower:
                    # NPC refuses to act or is locked in isolation
                    return False
            # Otherwise, allow action but behavior will be affected
        
        return True

    async def generate_dialogue(
        self, 
        player_input: str, 
        game_state: GameState
    ) -> str:
        """
        Generate NPC dialogue response.

        Args:
            player_input: Player's message
            game_state: Current GameState

        Returns:
            str: NPC dialogue response
        """
        npc = self._get_npc(game_state)
        if not npc:
            return "I'm not here right now..."
        
        if not npc.alive:
            return "..."
        
        try:
            # Get relationship level with player
            relationship_level = 0
            if "player" in npc.relationships:
                relationship_level = npc.relationships["player"].trust_level
            
            # Build dialogue prompt
            prompt = build_npc_dialogue_prompt(
                npc_data=npc.model_dump(),
                player_message=player_input,
                relationship_level=relationship_level,
                game_state=game_state
            )
            
            # Generate response using Gemini Flash (faster for dialogue)
            response = await self.gemini_client.generate(
                prompt=prompt,
                model="flash",
                temperature=0.8,  # Slightly higher for more natural dialogue
                max_tokens=150  # Keep dialogue concise
            )
            
            # Clean up response (remove quotes if wrapped)
            response = response.strip()
            if response.startswith('"') and response.endswith('"'):
                response = response[1:-1]
            if response.startswith("'") and response.endswith("'"):
                response = response[1:-1]
            
            logger.info(f"[NPCAgent] {npc.name} generated dialogue response")
            return response
            
        except Exception as e:
            logger.error(f"[NPCAgent] Error generating dialogue for {self.npc_id}: {e}")
            # Fallback response based on relationship
            if "player" in npc.relationships:
                trust = npc.relationships["player"].trust_level
                if trust >= 50:
                    return "I understand, but I'm having trouble responding right now."
                elif trust >= 0:
                    return "I'm not sure how to respond to that."
                else:
                    return "..."
            return "..."

    async def decide_action(self, game_state: GameState) -> Dict[str, Any]:
        """
        Decide NPC's autonomous action.

        Args:
            game_state: Current GameState

        Returns:
            dict: Chosen action with keys: action_type, target, description, reason
        """
        npc = self._get_npc(game_state)
        if not npc or not npc.alive:
            return {
                "action_type": "none",
                "target": None,
                "description": "NPC is unavailable",
                "reason": "NPC not found or not alive"
            }
        
        try:
            # Build NPC behavior prompt
            prompt = build_npc_prompt(
                npc_data=npc.model_dump(),
                game_state=game_state,
                context={}
            )
            
            # Generate action using Gemini Flash
            response = await self.gemini_client.generate(
                prompt=prompt,
                model="flash",
                temperature=0.6,  # Lower for more consistent decisions
                max_tokens=200
            )
            
            # Try to parse JSON response
            try:
                # Extract JSON from response (might have extra text)
                response = response.strip()
                if "```json" in response:
                    # Extract JSON from code block
                    start = response.find("```json") + 7
                    end = response.find("```", start)
                    response = response[start:end].strip()
                elif "```" in response:
                    # Extract from generic code block
                    start = response.find("```") + 3
                    end = response.find("```", start)
                    response = response[start:end].strip()
                
                # Parse JSON
                action = json.loads(response)
                
                # Validate required fields
                if not isinstance(action, dict):
                    raise ValueError("Action must be a dict")
                
                # Ensure required fields exist
                action.setdefault("action_type", "continue")
                action.setdefault("target", None)
                action.setdefault("description", "No description")
                action.setdefault("reason", "No reason given")
                
                logger.info(f"[NPCAgent] {npc.name} decided action: {action['action_type']}")
                return action
                
            except (json.JSONDecodeError, ValueError) as e:
                logger.warning(f"[NPCAgent] Failed to parse JSON response: {e}, response: {response}")
                # Fallback: return a default action
                return {
                    "action_type": "continue",
                    "target": None,
                    "description": npc.current_activity or "Continuing current task",
                    "reason": "Unable to parse AI response, using default"
                }
                
        except Exception as e:
            logger.error(f"[NPCAgent] Error deciding action for {self.npc_id}: {e}")
            # Fallback action
            return {
                "action_type": "continue",
                "target": None,
                "description": npc.current_activity or "Resting",
                "reason": f"Error occurred: {str(e)}"
            }

    async def act(
        self, 
        game_state: GameState, 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate NPC action (unified interface).

        Args:
            game_state: Current GameState
            context: Action context
                - "type": "dialogue" or "autonomous"
                - "player_input": (if type is "dialogue")
                - Other context info

        Returns:
            dict: NPC action result
        """
        action_type = context.get("type", "autonomous")
        
        if action_type == "dialogue":
            player_input = context.get("player_input", "")
            dialogue = await self.generate_dialogue(player_input, game_state)
            return {
                "type": "dialogue",
                "dialogue": dialogue,
                "npc_id": self.npc_id
            }
        else:
            # Autonomous action
            action = await self.decide_action(game_state)
            return {
                "type": "autonomous",
                "action": action,
                "npc_id": self.npc_id
            }
