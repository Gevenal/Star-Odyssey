"""AI output parsing utilities."""
from typing import Optional, Dict, Any


def parse_narration(ai_output: str) -> Dict[str, Any]:
    """
    Parse narration output into structured format.

    Args:
        ai_output: Raw AI narration output

    Returns:
        dict: Parsed narration with metadata
    """
    raise NotImplementedError


def parse_npc_action(ai_output: str) -> Dict[str, Any]:
    """
    Parse NPC action output.

    Args:
        ai_output: Raw NPC AI output

    Returns:
        dict: Structured NPC action data
    """
    raise NotImplementedError


def parse_world_event(ai_output: str) -> Dict[str, Any]:
    """
    Parse world event output.

    Args:
        ai_output: Raw world event output

    Returns:
        dict: Structured event data
    """
    raise NotImplementedError


def extract_state_updates(ai_output: str) -> Optional[Dict[str, Any]]:
    """
    Extract state updates from AI output.

    Args:
        ai_output: Raw AI output

    Returns:
        Optional[dict]: Extracted state updates or None
    """
    raise NotImplementedError


def sanitize_output(ai_output: str) -> str:
    """
    Sanitize AI output for safety.

    Args:
        ai_output: Raw AI output

    Returns:
        str: Sanitized output
    """
    raise NotImplementedError
