"""Helper utilities for NPC relationship management."""
from typing import Dict, Any, Optional
from app.models.npc import NPCState, NPCRelationship
from app.utils.logger import get_logger

logger = get_logger(__name__)


def format_relationships_for_ai_prompt(
    npc: NPCState,
    all_npcs: Dict[str, NPCState]
) -> str:
    """
    Format NPC relationships into a readable string for AI prompts.
    
    This helps Gemini understand the relationship context when generating
    NPC dialogue or actions.
    
    Args:
        npc: The NPC whose relationships to format
        all_npcs: Dictionary of all NPCs (for name lookup)
        
    Returns:
        Formatted string describing relationships
    """
    if not npc.relationships:
        return f"{npc.name} has no significant relationships with other crew members."
    
    lines = [f"{npc.name}'s relationships with the crew:"]
    
    for target_id, relationship in npc.relationships.items():
        # Find target NPC name
        target_npc = all_npcs.get(target_id)
        target_name = target_npc.name if target_npc else target_id
        
        # Get disposition
        disposition = relationship.get_disposition()
        
        # Build relationship description
        rel_desc = f"- {target_name}: {disposition.value} (trust: {relationship.trust_level})"
        
        # Add secret knowledge if any
        if relationship.secret_knowledge:
            secrets = ", ".join(relationship.secret_knowledge)
            rel_desc += f". Knows: {secrets}"
        
        # Add voice style if specified
        if relationship.voice_style:
            rel_desc += f". Speaks about/to them: {relationship.voice_style}"
        
        # Add relationship history
        if relationship.relationship_history:
            history = relationship.relationship_history[-1]  # Most recent
            rel_desc += f". History: {history}"
        
        lines.append(rel_desc)
    
    return "\n".join(lines)


def get_relationship_summary(
    npc1: NPCState,
    npc2: NPCState
) -> Dict[str, Any]:
    """
    Get summary of relationship between two NPCs.
    
    Args:
        npc1: First NPC
        npc2: Second NPC
        
    Returns:
        Dict with relationship summary
    """
    rel1 = npc1.relationships.get(npc2.id)
    rel2 = npc2.relationships.get(npc1.id)
    
    if not rel1 and not rel2:
        return {
            "has_relationship": False,
            "trust_level": 0,
            "disposition": "NEUTRAL"
        }
    
    # Use npc1's perspective as primary
    primary_rel = rel1 or rel2
    
    return {
        "has_relationship": True,
        "trust_level": primary_rel.trust_level,
        "disposition": primary_rel.get_disposition().value,
        "secret_knowledge": primary_rel.secret_knowledge.copy(),
        "voice_style": primary_rel.voice_style,
        "relationship_history": primary_rel.relationship_history.copy(),
        "is_bidirectional": rel1 is not None and rel2 is not None,
        "trust_asymmetric": rel1 and rel2 and rel1.trust_level != rel2.trust_level
    }


def update_relationship_after_event(
    npc1: NPCState,
    npc2: NPCState,
    trust_change: int,
    event_description: str
) -> None:
    """
    Update relationship after an in-game event.
    
    Args:
        npc1: First NPC
        npc2: Second NPC
        trust_change: Change in trust level (can be negative)
        event_description: Description of the event that caused the change
    """
    rel1 = npc1.relationships.get(npc2.id)
    rel2 = npc2.relationships.get(npc1.id)
    
    if rel1:
        rel1.trust_level = max(-100, min(100, rel1.trust_level + trust_change))
        rel1.relationship_history.append(event_description)
        logger.debug(f"Updated {npc1.name} -> {npc2.name}: trust now {rel1.trust_level}")
    
    if rel2:
        # Reverse relationship may change differently
        rel2.trust_level = max(-100, min(100, rel2.trust_level + trust_change))
        rel2.relationship_history.append(event_description)
        logger.debug(f"Updated {npc2.name} -> {npc1.name}: trust now {rel2.trust_level}")
