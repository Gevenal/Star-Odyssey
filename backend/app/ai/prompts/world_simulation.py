"""World simulation prompt building."""
from typing import Dict, Any


def build_world_event_prompt(
    game_state,
    turn_number: int
) -> str:
    """
    Build world event generation prompt.

    Args:
        game_state: Current GameState
        turn_number: Current turn number

    Returns:
        str: World event prompt
    """
    raise NotImplementedError


def build_hazard_prompt(
    location_id: str,
    game_state
) -> str:
    """
    Build location hazard prompt.

    Args:
        location_id: Location identifier
        game_state: Current GameState

    Returns:
        str: Hazard generation prompt
    """
    raise NotImplementedError


def format_world_state(game_state) -> str:
    """
    Format world state for prompt context.

    Args:
        game_state: Current GameState

    Returns:
        str: Formatted world state
    """
    raise NotImplementedError
