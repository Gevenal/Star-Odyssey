"""NPC action scheduling and coordination."""
from typing import List, Dict, Any, Optional
from app.models.game_state import GameState
from app.models.npc import NPCState
from app.ai.agents.npc_agent import NPCAgent
from app.utils.logger import get_logger
import random

logger = get_logger(__name__)


class NPCScheduler:
    """Manages NPC turn scheduling and action coordination."""

    def __init__(self, gemini_client, npc_repo=None):
        """
        Initialize NPC scheduler.

        Args:
            gemini_client: GeminiClient instance for AI generation
            npc_repo: NPCRepository instance (optional, not currently used)
        """
        self.gemini_client = gemini_client
        self.npc_repo = npc_repo
        self.npc_agents: Dict[str, NPCAgent] = {}

    def register_npc_agent(self, npc_id: str, agent: NPCAgent):
        """
        Register an NPC agent.

        Args:
            npc_id: NPC identifier
            agent: NPCAgent instance
        """
        self.npc_agents[npc_id] = agent
        logger.debug(f"[NPCScheduler] Registered agent for NPC: {npc_id}")

    def _get_or_create_agent(self, npc_id: str) -> NPCAgent:
        """Get existing agent or create new one."""
        if npc_id not in self.npc_agents:
            agent = NPCAgent(gemini_client=self.gemini_client, npc_id=npc_id)
            self.npc_agents[npc_id] = agent
        return self.npc_agents[npc_id]

    async def schedule_npc_turns(self, game_state: GameState) -> List[str]:
        """
        Determine which NPCs should act this turn.

        Args:
            game_state: Current GameState

        Returns:
            list[str]: NPC IDs scheduled to act
        """
        scheduled = []
        
        for npc_id, npc in game_state.npcs.items():
            # Only schedule alive NPCs
            if not npc.alive:
                continue
            
            # Skip ORACLE (AI entity, handled separately)
            if npc_id == "npc_ship_ai" or getattr(npc, 'is_ai', False):
                continue
            
            # Check if NPC can act
            agent = self._get_or_create_agent(npc_id)
            if not agent.can_act(game_state):
                continue
            
            # Decision logic: not all NPCs act every turn
            # Higher stress = more likely to act (they're reacting to crisis)
            # Lower stress = less likely (they're calm, doing routine tasks)
            
            # Base probability: 60% chance to act
            base_probability = 0.6
            
            # Stress modifier: stressed NPCs are more reactive
            stress_modifier = npc.stress_level / 100.0 * 0.3  # +0 to +0.3
            
            # Health modifier: injured NPCs less likely to act
            health_modifier = -((100 - npc.health) / 100.0) * 0.2  # -0 to -0.2
            
            # Final probability
            probability = base_probability + stress_modifier + health_modifier
            probability = max(0.3, min(0.9, probability))  # Clamp between 30% and 90%
            
            if random.random() < probability:
                scheduled.append(npc_id)
        
        logger.info(f"[NPCScheduler] Scheduled {len(scheduled)} NPCs to act: {scheduled}")
        return scheduled

    async def execute_npc_turn(
        self, 
        npc_id: str, 
        game_state: GameState
    ) -> Dict[str, Any]:
        """
        Execute a single NPC's turn.

        Args:
            npc_id: NPC identifier
            game_state: Current GameState

        Returns:
            dict: NPC action results with keys:
                - npc_id: NPC identifier
                - npc_name: NPC name
                - action_type: Type of action taken
                - description: Description of action
                - success: Whether action succeeded
                - state_changes: Any state changes made
        """
        npc = game_state.npcs.get(npc_id)
        if not npc or not npc.alive:
            return {
                "npc_id": npc_id,
                "npc_name": npc.name if npc else "Unknown",
                "action_type": "none",
                "description": "NPC not available",
                "success": False,
                "state_changes": {}
            }
        
        try:
            agent = self._get_or_create_agent(npc_id)
            
            # Get NPC's autonomous action decision
            action_result = await agent.decide_action(game_state)
            
            # Extract action details
            action_type = action_result.get("action_type", "continue")
            description = action_result.get("description", "No action")
            reason = action_result.get("reason", "")
            target = action_result.get("target")
            
            # Apply action effects (simplified - full implementation would use RulesEngine)
            state_changes = {}
            
            # Update NPC's current_activity based on action
            if action_type in ["repair", "continue", "help"]:
                state_changes["current_activity"] = description
            elif action_type == "rest":
                state_changes["current_activity"] = "resting"
                # Resting reduces stress slightly
                state_changes["stress_level"] = max(0, npc.stress_level - 2)
            elif action_type == "move":
                if target:
                    state_changes["location"] = target
            
            logger.info(f"[NPCScheduler] {npc.name} executed action: {action_type} - {description}")
            
            return {
                "npc_id": npc_id,
                "npc_name": npc.name,
                "action_type": action_type,
                "description": description,
                "reason": reason,
                "target": target,
                "success": True,
                "state_changes": state_changes
            }
            
        except Exception as e:
            logger.error(f"[NPCScheduler] Error executing turn for {npc_id}: {e}")
            return {
                "npc_id": npc_id,
                "npc_name": npc.name if npc else "Unknown",
                "action_type": "error",
                "description": f"Error: {str(e)}",
                "success": False,
                "state_changes": {}
            }

    async def execute_all_npc_turns(
        self, 
        game_state: GameState
    ) -> List[Dict[str, Any]]:
        """
        Execute all scheduled NPC turns.

        Args:
            game_state: Current GameState

        Returns:
            list[dict]: All NPC action results
        """
        # Schedule which NPCs should act
        scheduled_npcs = await self.schedule_npc_turns(game_state)
        
        if not scheduled_npcs:
            logger.info("[NPCScheduler] No NPCs scheduled to act this turn")
            return []
        
        # Execute each NPC's turn
        results = []
        for npc_id in scheduled_npcs:
            try:
                result = await self.execute_npc_turn(npc_id, game_state)
                results.append(result)
            except Exception as e:
                logger.error(f"[NPCScheduler] Failed to execute turn for {npc_id}: {e}")
                results.append({
                    "npc_id": npc_id,
                    "npc_name": "Unknown",
                    "action_type": "error",
                    "description": f"Execution failed: {str(e)}",
                    "success": False,
                    "state_changes": {}
                })
        
        logger.info(f"[NPCScheduler] Executed {len(results)} NPC turns")
        return results
