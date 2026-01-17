"""Narrator prompt building."""
from typing import Dict, Any


def build_narrator_prompt(
    game_state,
    player_action: str,
    context: Dict[str, Any]
) -> str:
    """
    Build narration prompt for Gemini Pro.

    Args:
        game_state: Current GameState
        player_action: Player's action text
        context: Additional context (history, etc.)

    Returns:
        str: Complete narration prompt
    """
    raise NotImplementedError


def build_ending_prompt(
    game_state,
    ending_type: str
) -> str:
    """
    Build ending narration prompt.

    Args:
        game_state: Final GameState
        ending_type: Type of ending

    Returns:
        str: Ending narration prompt
    """
    raise NotImplementedError


def format_game_context(game_state) -> str:
    """
    Format game state into context for narration.

    Args:
        game_state: Current GameState

    Returns:
        str: Formatted context string
    """
    raise NotImplementedError
