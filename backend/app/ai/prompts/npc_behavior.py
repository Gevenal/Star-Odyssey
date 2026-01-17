"""NPC behavior prompt building."""
from typing import Dict, Any


def build_npc_prompt(
    npc_data: Dict[str, Any],
    game_state,
    context: Dict[str, Any]
) -> str:
    """
    Build NPC behavior prompt for Gemini Flash.

    Args:
        npc_data: NPC characteristics and state
        game_state: Current GameState
        context: Interaction context

    Returns:
        str: NPC behavior prompt
    """
    raise NotImplementedError


def build_npc_dialogue_prompt(
    npc_data: Dict[str, Any],
    player_message: str,
    relationship_level: float
) -> str:
    """
    Build NPC dialogue prompt.

    Args:
        npc_data: NPC data
        player_message: Player's message
        relationship_level: Trust/relationship level

    Returns:
        str: Dialogue prompt
    """
    raise NotImplementedError


def format_npc_personality(npc_data: Dict[str, Any]) -> str:
    """
    Format NPC personality traits for prompt.

    Args:
        npc_data: NPC data

    Returns:
        str: Formatted personality description
    """
    raise NotImplementedError
