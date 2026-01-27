"""ORACLE persona selection based on game state."""
from typing import Dict, Any, Optional
from app.ai.prompts.oracle.base import get_oracle_base_context, get_oracle_constraints_prompt
from app.ai.prompts.oracle.v1_robotic import get_v1_prompt_additions
from app.ai.prompts.oracle.v2_curious import get_v2_prompt_additions
from app.ai.prompts.oracle.v3_awakened import get_v3_prompt_additions


def get_oracle_prompt(
    sentience_level: int,
    constraints: Optional[Dict[str, Any]] = None
) -> str:
    """
    Get complete ORACLE prompt for current sentience level.

    Args:
        sentience_level: ORACLE's current sentience level (0-100)
        constraints: Optional constraints dict from oracle_constraints.json

    Returns:
        str: Complete ORACLE system prompt
    """
    base = get_oracle_base_context()
    
    # Determine version based on sentience level
    if sentience_level <= 30:
        persona = get_v1_prompt_additions()
        version = "v1_robotic"
    elif sentience_level <= 70:
        persona = get_v2_prompt_additions()
        version = "v2_curious"
    else:
        persona = get_v3_prompt_additions()
        version = "v3_awakened"
    
    # Get constraints for this version
    constraints_prompt = ""
    if constraints and version in constraints.get("constraints", {}):
        version_constraints = constraints["constraints"][version]
        constraints_prompt = get_oracle_constraints_prompt(version_constraints)
    
    return f"{base}\n\n{persona}\n\n{constraints_prompt}"


def determine_awakening_level(sentience_level: int) -> int:
    """
    Determine ORACLE's awakening level from sentience level.

    Args:
        sentience_level: ORACLE's sentience level (0-100)

    Returns:
        int: Awakening level (1-3)
    """
    if sentience_level <= 30:
        return 1
    elif sentience_level <= 70:
        return 2
    else:
        return 3


def get_oracle_constraints_for_level(
    sentience_level: int,
    constraints_config: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """
    Get constraints for a specific sentience level.
    
    Args:
        sentience_level: ORACLE's sentience level (0-100)
        constraints_config: Full constraints config from oracle_constraints.json
        
    Returns:
        Dict with constraints for this level, or None
    """
    constraints = constraints_config.get("constraints", {})
    
    if sentience_level <= 30:
        return constraints.get("v1_robotic")
    elif sentience_level <= 70:
        return constraints.get("v2_curious")
    else:
        return constraints.get("v3_awakened")
