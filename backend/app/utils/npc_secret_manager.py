"""NPC secret reveal management."""
from typing import List, Optional, Dict, Any
from app.models.npc import NPCState, NPCSecret
from app.models.game_state import GameState
from app.utils.logger import get_logger
import re

logger = get_logger(__name__)


class NPCSecretManager:
    """Manages NPC secret revelation based on conditions."""

    @staticmethod
    def check_reveal_condition(
        secret: NPCSecret,
        npc: NPCState,
        game_state: GameState,
        context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Check if a secret's reveal condition is met.

        Args:
            secret: NPCSecret to check
            npc: NPC that has this secret
            game_state: Current GameState
            context: Optional context (e.g., {"action_type": "confrontation", "investigation_complete": True})

        Returns:
            bool: True if condition is met
        """
        if not secret.reveal_condition:
            return False
        
        if secret.known_by_player:
            return False  # Already revealed
        
        condition = secret.reveal_condition.lower()
        context = context or {}
        
        # Get player relationship trust level
        player_trust = 0
        if "player" in npc.relationships:
            player_trust = npc.relationships["player"].trust_level
        
        # Parse condition string
        # Support conditions like:
        # - "trust_level > 60"
        # - "trust_level > 50 or crisis_escalation"
        # - "confrontation or trust_level > 75"
        # - "investigation or trust_level < -20"
        
        # Check for trust level conditions
        trust_patterns = [
            r"trust_level\s*>\s*(\d+)",
            r"trust_level\s*>=\s*(\d+)",
            r"trust_level\s*<\s*(\d+)",
            r"trust_level\s*<=\s*(\d+)",
            r"trust_level\s*==\s*(\d+)",
            r"trust_level\s*>=\s*(\d+)",
        ]
        
        trust_conditions_met = []
        for pattern in trust_patterns:
            matches = re.findall(pattern, condition)
            for match in matches:
                threshold = int(match)
                if ">" in pattern and "=" not in pattern:
                    trust_conditions_met.append(player_trust > threshold)
                elif ">=" in pattern:
                    trust_conditions_met.append(player_trust >= threshold)
                elif "<" in pattern and "=" not in pattern:
                    trust_conditions_met.append(player_trust < threshold)
                elif "<=" in pattern:
                    trust_conditions_met.append(player_trust <= threshold)
                elif "==" in pattern:
                    trust_conditions_met.append(player_trust == threshold)
        
        # Check for keyword conditions
        keyword_conditions = {
            "confrontation": context.get("action_type") == "confrontation" or context.get("confrontation", False),
            "investigation": context.get("action_type") == "investigation" or context.get("investigation_complete", False),
            "crisis_escalation": game_state.world.panic_level > 70 if hasattr(game_state.world, 'panic_level') else False,
            "guilt_overwhelming": npc.stress_level > 80 and player_trust > 50,
            "emotional_moment": context.get("emotional_moment", False),
            "medical_scan": context.get("action_type") == "medical_scan" or context.get("medical_scan", False),
            "oracle_sentience_revealed": game_state.oracle_sentience_level >= 3 if hasattr(game_state, 'oracle_sentience_level') else False,
        }
        
        keyword_conditions_met = []
        for keyword, is_met in keyword_conditions.items():
            if keyword in condition:
                keyword_conditions_met.append(is_met)
        
        # Combine conditions with OR/AND logic
        # Simple heuristic: if condition contains "or", use OR logic; otherwise use AND
        if " or " in condition:
            # OR logic: any condition met
            return any(trust_conditions_met) or any(keyword_conditions_met)
        else:
            # AND logic: all conditions must be met
            all_trust_met = all(trust_conditions_met) if trust_conditions_met else True
            all_keyword_met = all(keyword_conditions_met) if keyword_conditions_met else True
            return all_trust_met and all_keyword_met

    @staticmethod
    def check_and_reveal_secrets(
        npc: NPCState,
        game_state: GameState,
        context: Optional[Dict[str, Any]] = None
    ) -> List[NPCSecret]:
        """
        Check all NPC secrets and reveal those that meet conditions.

        Args:
            npc: NPC to check secrets for
            game_state: Current GameState
            context: Optional context for condition checking

        Returns:
            List[NPCSecret]: List of newly revealed secrets
        """
        revealed_secrets = []
        
        for secret in npc.secrets:
            if secret.known_by_player:
                continue  # Already revealed
            
            if NPCSecretManager.check_reveal_condition(secret, npc, game_state, context):
                secret.known_by_player = True
                revealed_secrets.append(secret)
                logger.info(f"[NPCSecretManager] Secret revealed: {secret.id} for NPC {npc.id}")
        
        return revealed_secrets

    @staticmethod
    def update_player_discovered_secrets(
        game_state: GameState,
        revealed_secrets: List[NPCSecret],
        npc_id: str
    ) -> None:
        """
        Update player's discovered_secrets list.

        Args:
            game_state: Current GameState
            revealed_secrets: List of newly revealed secrets
            npc_id: NPC ID that revealed these secrets
        """
        if not revealed_secrets:
            return
        
        for secret in revealed_secrets:
            # PlayerState.discovered_secrets is List[str] (secret IDs)
            # Just add the secret ID if not already present
            if secret.id not in game_state.player.discovered_secrets:
                game_state.player.discovered_secrets.append(secret.id)
                logger.info(f"[NPCSecretManager] Added secret {secret.id} to player discovered_secrets")
