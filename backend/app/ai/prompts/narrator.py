"""Narrator prompt building."""
from typing import Dict, Any


def format_game_context(state: Dict[str, Any], turn_history: list = None) -> str:
    """
    Format game state dict into a readable context string for the AI.

    Args:
        state: GameStateManager.state or snapshot["state"]
        turn_history: optional list of recent turn entries (from GameStateManager.turn_history)

    Returns:
        str: Formatted context (resources, player, turn, etc.)
    """
    lines = []
    meta = state.get("game_meta", {})
    lines.append(f"Turn: {meta.get('current_turn', 1)}, Day: {meta.get('current_day', 1)}, Phase: {meta.get('game_phase', 'playing')}")

    resources = state.get("resources", {})
    if resources:
        res_parts = [f"{k}: {v}" if isinstance(v, (int, float)) else f"{k}: {v.get('current', v)}" for k, v in resources.items()]
        lines.append("Resources: " + ", ".join(res_parts))

    player = state.get("player", {})
    lines.append(
        f"Player: {player.get('name', 'Unknown')}, health={player.get('health', 100)}, "
        f"location={player.get('current_location', player.get('location', 'unknown'))}"
    )

    npcs = state.get("npcs", {})
    if npcs:
        npc_summary = [f"{n.get('name', kid)}" for kid, n in list(npcs.items())[:5]]
        lines.append("Crew present: " + ", ".join(npc_summary))

    history = turn_history or state.get("turn_history", [])
    if history:
        lines.append("Recent: " + str(history[-2:]))

    return "\n".join(lines)


def build_narrator_prompt(
    game_state: Dict[str, Any],
    player_action: str,
    action_id: str = "",
    context: Dict[str, Any] = None,
) -> str:
    """
    Build the user prompt for Gemini narrator (action → GameActionResponse).

    Args:
        game_state: state dict (GameStateManager.state or snapshot["state"])
        player_action: Player's action text
        action_id: action_id from PlayerAction (e.g. "repair_reactor")
        context: optional extra (e.g. {"history": [...]})

    Returns:
        str: User prompt for generate_structured
    """
    ctx = context or {}
    state_str = format_game_context(game_state, turn_history=ctx.get("turn_history"))

    prompt = f"""You are the narrator for the space survival game star-Odyssey. Given the current state and the player's action, respond with a JSON object that includes: success, narration, mood, state_changes, resource_changes, npc_reactions, available_actions, trigger_ending, ending_id, oracle_message, confidence_level.

CURRENT STATE:
{state_str}

PLAYER ACTION (action_id={action_id or 'unknown'}):
{player_action}
"""
    if ctx.get("history"):
        prompt += f"\nRECENT EVENTS:\n{ctx['history']}\n"

    prompt += """
Generate a short, immersive narration (2–4 sentences) for the outcome. Declare state_changes and resource_changes that fit the action. Set trigger_ending=true only if the player clearly died, everyone died, or a defined victory is reached. Use the JSON schema provided in the system instruction."""
    return prompt


def get_narrator_system_instruction() -> str:
    """System instruction for the narrator (to be merged with JSON schema by GeminiClient)."""
    return (
        "You are the narrator for Odyssey-7, an AI-driven space survival game. "
        "Describe outcomes in past tense, 2–4 sentences. "
        "Only declare state_changes and resource_changes that are plausible. "
        "Respond ONLY with a valid JSON object; no extra text."
    )


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
    return f"""Generate a dramatic ending narration for a sci-fi survival game.
ENDING TYPE: {ending_type.upper()}
FINAL STATE: {game_state}
Write 300–500 words."""
