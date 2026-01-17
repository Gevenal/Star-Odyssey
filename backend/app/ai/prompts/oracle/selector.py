"""ORACLE persona selection based on game state."""
from app.ai.prompts.oracle.base import get_oracle_base_context
from app.ai.prompts.oracle.v1_robotic import get_v1_prompt_additions
from app.ai.prompts.oracle.v2_curious import get_v2_prompt_additions
from app.ai.prompts.oracle.v3_awakened import get_v3_prompt_additions


def get_oracle_prompt(awakening_level: int) -> str:
    """
    Get complete ORACLE prompt for current awakening level.

    Args:
        awakening_level: ORACLE's current awakening (1-3)

    Returns:
        str: Complete ORACLE system prompt
    """
    raise NotImplementedError


def determine_awakening_level(game_state) -> int:
    """
    Determine ORACLE's awakening level from game state.

    Args:
        game_state: Current GameState

    Returns:
        int: Awakening level (1-3)
    """
    raise NotImplementedError
