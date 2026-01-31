"""NPC behavior prompt building."""
from typing import Dict, Any, Optional
from app.models.npc import NPCState
from app.game_data.loader import GameDataLoader
from app.utils.npc_generator import NPCGenerator
from pathlib import Path


def _get_npc_generator() -> Optional[NPCGenerator]:
    """Get NPCGenerator instance for formatting personality."""
    try:
        from pathlib import Path
        app_dir = Path(__file__).resolve().parents[2]  # backend/app
        data_dir = app_dir / "game_data"
        
        data_loader = GameDataLoader(data_dir=data_dir)
        trait_pool_data = data_loader.load_personality_traits()
        npc_templates = data_loader.load_npc_templates()
        
        # Convert traits list to dict by category
        trait_pool_dict = {}
        for trait in trait_pool_data.traits:
            category = trait.category
            if category not in trait_pool_dict:
                trait_pool_dict[category] = []
            trait_pool_dict[category].append(trait)
        
        return NPCGenerator(
            trait_pool=trait_pool_dict,
            npc_templates=npc_templates
        )
    except Exception as e:
        print(f"[npc_behavior] Warning: Failed to create NPCGenerator: {e}")
        return None


def format_npc_personality(npc_data: Dict[str, Any]) -> str:
    """
    Format NPC personality traits for prompt.

    Args:
        npc_data: NPC data (can be dict or NPCState)

    Returns:
        str: Formatted personality description
    """
    try:
        # Convert dict to NPCState if needed
        if isinstance(npc_data, dict):
            npc = NPCState(**npc_data)
        else:
            npc = npc_data
        
        generator = _get_npc_generator()
        if generator:
            return generator.get_personality_prompt_instructions(npc)
        
        # Fallback: basic formatting
        personality = npc.personality
        parts = [
            f"Core Value: {personality.core_value}",
            f"Social Style: {personality.social_style}",
            f"Stress Response: {personality.stress_response}",
            f"Decision Making: {personality.decision_making}",
            f"Morality: {personality.morality}",
        ]
        if personality.speech_pattern:
            parts.append(f"Speech Pattern: {personality.speech_pattern}")
        if personality.quirks:
            parts.append(f"Quirks: {', '.join(personality.quirks)}")
        
        return "\n".join(parts)
    except Exception as e:
        print(f"[npc_behavior] Error formatting personality: {e}")
        return "Personality information unavailable."


def build_npc_dialogue_prompt(
    npc_data: Dict[str, Any],
    player_message: str,
    relationship_level: float,
    game_state: Optional[Any] = None
) -> str:
    """
    Build NPC dialogue prompt.

    Args:
        npc_data: NPC data (dict or NPCState)
        player_message: Player's message
        relationship_level: Trust/relationship level (-100 to 100)
        game_state: Optional game state for context

    Returns:
        str: Dialogue prompt
    """
    try:
        # Convert dict to NPCState if needed
        if isinstance(npc_data, dict):
            npc = NPCState(**npc_data)
        else:
            npc = npc_data
        
        # Format personality
        personality_text = format_npc_personality(npc)
        
        # Determine relationship description
        if relationship_level >= 75:
            relationship_desc = "very loyal and trusting"
        elif relationship_level >= 25:
            relationship_desc = "friendly and cooperative"
        elif relationship_level >= -25:
            relationship_desc = "neutral"
        elif relationship_level >= -75:
            relationship_desc = "unfriendly and suspicious"
        else:
            relationship_desc = "hostile and untrusting"
        
        # Get current state info
        stress_info = ""
        if npc.stress_level >= 75:
            stress_info = f"\n⚠️ CRITICAL: {npc.name} is highly stressed ({npc.stress_level}%) and may be in breakdown state."
        elif npc.stress_level >= 50:
            stress_info = f"\n⚠️ {npc.name} is under significant stress ({npc.stress_level}%)."
        
        breakdown_info = ""
        breakdown_instructions = ""
        if npc.is_in_breakdown and npc.breakdown_behavior:
            breakdown_info = f"\n🚨 BREAKDOWN: {npc.breakdown_behavior}"
            # Add specific breakdown behavior instructions
            breakdown_lower = npc.breakdown_behavior.lower()
            if "refuse" in breakdown_lower or "reject" in breakdown_lower:
                breakdown_instructions = "\n⚠️ CRITICAL: You are in breakdown and may REFUSE to help or cooperate. You might say 'no' or ignore requests."
            elif "lie" in breakdown_lower or "deceive" in breakdown_lower:
                breakdown_instructions = "\n⚠️ CRITICAL: You are in breakdown and may LIE or give misleading information."
            elif "panic" in breakdown_lower or "fear" in breakdown_lower:
                breakdown_instructions = "\n⚠️ CRITICAL: You are panicking. Your responses should be erratic, fearful, or irrational."
            elif "aggressive" in breakdown_lower or "hostile" in breakdown_lower:
                breakdown_instructions = "\n⚠️ CRITICAL: You are in breakdown and may be AGGRESSIVE or HOSTILE in your responses."
            else:
                breakdown_instructions = f"\n⚠️ CRITICAL: You are in breakdown state. Your behavior: {npc.breakdown_behavior}"
        
        # Get current activity
        activity_info = ""
        if npc.current_activity:
            activity_info = f"\nCurrent Activity: {npc.current_activity}"
        
        # Get goals
        goals_info = ""
        if npc.goals:
            goals_info = f"\nCurrent Goals: {', '.join(npc.goals)}"
        
        # Get relationship history with player
        history_info = ""
        if "player" in npc.relationships:
            rel = npc.relationships["player"]
            if rel.relationship_history:
                recent_history = rel.relationship_history[-3:]  # Last 3 events
                history_info = f"\nRecent History with Player: {'; '.join(recent_history)}"
        
        prompt = f"""You are {npc.name}, the {npc.role} on a damaged spaceship in crisis.

PERSONALITY & BEHAVIOR:
{personality_text}

CURRENT STATE:
- Health: {npc.health}%
- Stress Level: {npc.stress_level}%{stress_info}{breakdown_info}{breakdown_instructions}
- Location: {npc.location}{activity_info}{goals_info}

RELATIONSHIP WITH PLAYER:
- Trust Level: {relationship_level}/100 ({relationship_desc}){history_info}

CONTEXT:
The ship is in crisis. Systems are failing, resources are depleting, and the crew is under pressure.
You must respond naturally based on your personality, current stress level, and relationship with the player.

PLAYER'S MESSAGE:
"{player_message}"

INSTRUCTIONS:
1. Respond as {npc.name} would, based on your personality traits above
2. Your response should reflect your relationship with the player ({relationship_desc})
3. Consider your current stress level and state of mind
4. Keep your response concise (1-3 sentences, max 100 words)
5. Stay in character - don't break the fourth wall
6. {breakdown_instructions if breakdown_instructions else "You are functioning normally."}

Respond now as {npc.name}:"""
        
        return prompt
    except Exception as e:
        print(f"[npc_behavior] Error building dialogue prompt: {e}")
        return f"Error: {e}"


def build_npc_prompt(
    npc_data: Dict[str, Any],
    game_state,
    context: Dict[str, Any]
) -> str:
    """
    Build NPC behavior prompt for Gemini Flash (autonomous actions).

    Args:
        npc_data: NPC characteristics and state (dict or NPCState)
        game_state: Current GameState
        context: Interaction context (optional)

    Returns:
        str: NPC behavior prompt
    """
    try:
        # Convert dict to NPCState if needed
        if isinstance(npc_data, dict):
            npc = NPCState(**npc_data)
        else:
            npc = npc_data
        
        # Format personality
        personality_text = format_npc_personality(npc)
        
        # Get world state summary
        world_summary = ""
        if hasattr(game_state, 'world'):
            world = game_state.world
            if hasattr(world, 'resources'):
                resources = world.resources
                world_summary = f"""
WORLD STATE:
- Oxygen: {getattr(resources, 'oxygen_level', {}).get('current', 'N/A') if isinstance(getattr(resources, 'oxygen_level', {}), dict) else getattr(resources, 'oxygen_level', 'N/A')}%
- Power: {getattr(resources, 'power_level', {}).get('current', 'N/A') if isinstance(getattr(resources, 'power_level', {}), dict) else getattr(resources, 'power_level', 'N/A')}%
- Crew Morale: {getattr(world, 'crew_morale', 'N/A')}
- Panic Level: {getattr(world, 'panic_level', 'N/A')}"""
        
        # Get other NPCs at same location
        location_npcs = []
        if hasattr(game_state, 'npcs'):
            for other_npc_id, other_npc in game_state.npcs.items():
                if other_npc_id != npc.id and other_npc.alive and other_npc.location == npc.location:
                    location_npcs.append(f"{other_npc.name} ({other_npc.role})")
        
        location_info = ""
        if location_npcs:
            location_info = f"\nOther NPCs at {npc.location}: {', '.join(location_npcs)}"
        
        # Stress and breakdown info
        stress_info = ""
        breakdown_constraints = ""
        if npc.stress_level >= 75:
            stress_info = f"\n⚠️ CRITICAL STRESS: {npc.stress_level}% - You are highly stressed and may not think clearly."
        if npc.is_in_breakdown:
            stress_info += f"\n🚨 BREAKDOWN STATE: {npc.breakdown_behavior}"
            # Add breakdown behavior constraints
            breakdown_lower = npc.breakdown_behavior.lower()
            if "refuse" in breakdown_lower or "reject" in breakdown_lower:
                breakdown_constraints = "\n⚠️ BREAKDOWN CONSTRAINT: You may REFUSE to help others or follow orders. Consider choosing 'rest' or 'continue' instead of helping."
            elif "panic" in breakdown_lower or "fear" in breakdown_lower:
                breakdown_constraints = "\n⚠️ BREAKDOWN CONSTRAINT: You are panicking. Your actions may be irrational or focused on self-preservation."
            elif "aggressive" in breakdown_lower:
                breakdown_constraints = "\n⚠️ BREAKDOWN CONSTRAINT: You are in breakdown and may act aggressively or destructively."
            elif "isolate" in breakdown_lower or "lock" in breakdown_lower:
                breakdown_constraints = "\n⚠️ BREAKDOWN CONSTRAINT: You are isolating yourself. Consider actions that keep you away from others."
        
        prompt = f"""You are {npc.name}, the {npc.role} on a damaged spaceship in crisis.

PERSONALITY & BEHAVIOR:
{personality_text}

YOUR CURRENT STATE:
- Health: {npc.health}%
- Stress: {npc.stress_level}%{stress_info}{breakdown_constraints}
- Location: {npc.location}{location_info}
- Current Activity: {npc.current_activity or "None"}
- Goals: {', '.join(npc.goals) if npc.goals else "None"}

{world_summary}

TASK:
Decide what action you should take this turn based on:
1. Your personality and current mental state
2. Your goals and responsibilities
3. The crisis situation
4. Your location and who else is there
5. Your breakdown state (if applicable){breakdown_constraints}

Choose ONE action from:
- Continue current activity (if applicable)
- Move to another location (if urgent)
- Repair/maintain systems
- Help another crew member
- Rest/recover (if health/stress is low)
- Investigate something suspicious
- Communicate with crew
- Other action appropriate to your role and situation

{breakdown_constraints}

Respond in JSON format:
{{
    "action_type": "repair|move|help|rest|investigate|communicate|continue|other",
    "target": "location_id or npc_id or system_name or null",
    "description": "Brief description of what you're doing (1-2 sentences)",
    "reason": "Why you chose this action"
}}"""
        
        return prompt
    except Exception as e:
        print(f"[npc_behavior] Error building NPC prompt: {e}")
        return f"Error: {e}"
