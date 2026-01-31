"""NPC item giving and trading system."""
from typing import Dict, Any, Optional, List
from app.models.npc import NPCState
from app.models.game_state import GameState
from app.utils.logger import get_logger

logger = get_logger(__name__)


class NPCItemManager:
    """Manages NPC item giving and trading."""

    @staticmethod
    def npc_give_item_to_player(
        npc: NPCState,
        player_state,
        item_id: str,
        reason: str = "gift"
    ) -> Dict[str, Any]:
        """
        NPC gives an item to player.

        Args:
            npc: NPC giving the item
            player_state: Player state
            item_id: Item ID to give
            reason: Reason for giving

        Returns:
            dict: Result of item transfer
        """
        if item_id not in npc.inventory:
            return {
                "success": False,
                "reason": f"{npc.name} doesn't have {item_id}"
            }
        
        # Remove from NPC inventory
        npc.inventory.remove(item_id)
        
        # Add to player inventory
        if item_id not in player_state.inventory:
            player_state.inventory.append(item_id)
        
        # Update relationship (gift increases trust)
        if "player" in npc.relationships:
            rel = npc.relationships["player"]
            rel.trust_level = min(100, rel.trust_level + 5)
            rel.relationship_history.append(f"Gave {item_id} to player ({reason})")
            if len(rel.relationship_history) > 10:
                rel.relationship_history = rel.relationship_history[-10:]
        
        logger.info(f"[NPCItemManager] {npc.name} gave {item_id} to player")
        
        return {
            "success": True,
            "item_id": item_id,
            "reason": reason,
            "trust_increase": 5
        }

    @staticmethod
    def check_npc_willing_to_give(
        npc: NPCState,
        item_id: str,
        game_state: GameState
    ) -> bool:
        """
        Check if NPC is willing to give an item.

        Args:
            npc: NPC to check
            item_id: Item to check
            game_state: Current GameState

        Returns:
            bool: True if NPC is willing
        """
        if item_id not in npc.inventory:
            return False
        
        # Check trust level
        player_trust = 0
        if "player" in npc.relationships:
            player_trust = npc.relationships["player"].trust_level
        
        # High trust = more willing
        if player_trust >= 60:
            return True
        elif player_trust >= 30:
            # Medium trust - depends on item value
            valuable_items = ["captain_keycard", "sidearm", "medical_scanner"]
            if item_id not in valuable_items:
                return True
        elif player_trust < 0:
            return False  # Low trust - won't give
        
        return False

    @staticmethod
    def npc_request_item_from_player(
        npc: NPCState,
        player_state,
        item_id: str,
        reason: str = "need"
    ) -> Dict[str, Any]:
        """
        NPC requests an item from player.

        Args:
            npc: NPC requesting
            player_state: Player state
            item_id: Item requested
            reason: Reason for request

        Returns:
            dict: Request result
        """
        if item_id not in player_state.inventory:
            return {
                "success": False,
                "reason": f"Player doesn't have {item_id}"
            }
        
        # Check if NPC should request (based on role and situation)
        should_request = False
        
        if npc.role in ["Medical Officer", "Chief Medical Officer"]:
            if item_id in ["medical_scanner", "trauma_kit", "medkit"]:
                should_request = True
        
        elif npc.role in ["Engineer", "Chief Engineer"]:
            if item_id in ["multitool", "repair_kit", "access_card_engineering"]:
                should_request = True
        
        if not should_request:
            return {
                "success": False,
                "reason": f"{npc.name} doesn't need {item_id}"
            }
        
        # Transfer item
        player_state.inventory.remove(item_id)
        if item_id not in npc.inventory:
            npc.inventory.append(item_id)
        
        # Update relationship
        if "player" in npc.relationships:
            rel = npc.relationships["player"]
            rel.trust_level = min(100, rel.trust_level + 10)
            rel.relationship_history.append(f"Player gave {item_id} ({reason})")
            if len(rel.relationship_history) > 10:
                rel.relationship_history = rel.relationship_history[-10:]
        
        logger.info(f"[NPCItemManager] Player gave {item_id} to {npc.name}")
        
        return {
            "success": True,
            "item_id": item_id,
            "reason": reason,
            "trust_increase": 10
        }
