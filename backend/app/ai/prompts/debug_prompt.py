"""Debug prompt for AI-powered game state analysis."""
from typing import Dict, Any, List
from app.models.game_state import GameState


def build_debug_risk_analysis_prompt(game_state: GameState) -> str:
    """
    Build prompt for AI to analyze game state risks.
    
    Args:
        game_state: Current game state
        
    Returns:
        str: Prompt for risk analysis
    """
    prompt_parts = []
    
    prompt_parts.append("# Debug Mode: Game State Risk Analysis")
    prompt_parts.append("")
    prompt_parts.append("You are analyzing the current game state to identify risks and dangers.")
    prompt_parts.append("Provide a structured analysis in JSON format.")
    prompt_parts.append("")
    
    # Current state summary
    prompt_parts.append("## Current Game State")
    prompt_parts.append(f"Day: {game_state.world.day}, Turn: {game_state.turn_count}")
    prompt_parts.append("")
    
    # Resources
    prompt_parts.append("### Resources")
    resources = game_state.world.resources
    prompt_parts.append(f"Oxygen: {resources.oxygen_level.current}% (critical: {resources.oxygen_level.critical_threshold}%)")
    prompt_parts.append(f"Power: {resources.power_level.current}%")
    prompt_parts.append(f"Fuel: {resources.fuel_reserves.current}%")
    prompt_parts.append(f"Medical Supplies: {resources.medical_supplies.current}%")
    prompt_parts.append(f"Food & Water: {resources.food_water.current}%")
    prompt_parts.append(f"Repair Materials: {resources.repair_materials.current}%")
    prompt_parts.append("")
    
    # Ship systems
    prompt_parts.append("### Ship Systems")
    systems = game_state.world.ship_systems
    prompt_parts.append(f"Reactor Integrity: {systems.reactor_integrity.current}%")
    prompt_parts.append(f"Hull Integrity: {systems.hull_integrity.current}%")
    prompt_parts.append(f"Life Support Efficiency: {systems.life_support_efficiency.current}%")
    prompt_parts.append(f"Navigation Systems: {systems.navigation_systems.current}%")
    prompt_parts.append(f"Communications Array: {systems.communications_array.current}%")
    prompt_parts.append(f"Escape Pods Ready: {systems.escape_pods_ready.current}")
    prompt_parts.append("")
    
    # Crew status
    prompt_parts.append("### Crew Status")
    prompt_parts.append(f"Crew Morale: {game_state.world.crew_morale}")
    prompt_parts.append(f"Crew Cohesion: {game_state.world.crew_cohesion}")
    prompt_parts.append(f"Panic Level: {game_state.world.panic_level}")
    prompt_parts.append("")
    
    # NPC status
    alive_npcs = [npc for npc in game_state.npcs.values() if npc.alive]
    prompt_parts.append(f"Alive NPCs: {len(alive_npcs)}/{len(game_state.npcs)}")
    for npc in alive_npcs:
        stress_status = "⚠️ PANIC" if npc.is_in_panic() else "OK" if npc.stress_level < 50 else "STRESSED"
        prompt_parts.append(f"  - {npc.name} ({npc.role}): Health {npc.health}%, Stress {npc.stress_level}% ({stress_status})")
    prompt_parts.append("")
    
    # Player status
    prompt_parts.append("### Player Status")
    prompt_parts.append(f"Health: {game_state.player.health}%")
    prompt_parts.append(f"Location: {game_state.player.current_location}")
    prompt_parts.append("")
    
    # Analysis request
    prompt_parts.append("## Analysis Request")
    prompt_parts.append("Analyze this game state and provide:")
    prompt_parts.append("")
    prompt_parts.append("1. **top_3_risks**: The three most immediate threats that could end the game")
    prompt_parts.append("   - Format: [\"Risk description\", \"Another risk\", \"Third risk\"]")
    prompt_parts.append("")
    prompt_parts.append("2. **hidden_cascades**: Hidden chain reactions that might not be obvious")
    prompt_parts.append("   - Example: \"If oxygen drops below 20%, NPCs will panic and may refuse orders\"")
    prompt_parts.append("   - Format: [\"Cascade 1\", \"Cascade 2\", ...]")
    prompt_parts.append("")
    prompt_parts.append("3. **misleading_metrics**: Metrics that look safe but are actually dangerous")
    prompt_parts.append("   - Example: \"Crew morale at 60 seems OK, but panic level is 75 - crew is on edge\"")
    prompt_parts.append("   - Format: [\"Metric 1\", \"Metric 2\", ...]")
    prompt_parts.append("")
    prompt_parts.append("4. **recommended_actions**: Action IDs the player should prioritize")
    prompt_parts.append("   - Format: [\"action_id_1\", \"action_id_2\", ...]")
    prompt_parts.append("")
    prompt_parts.append("Respond in JSON format:")
    prompt_parts.append("```json")
    prompt_parts.append("{")
    prompt_parts.append('  "top_3_risks": ["...", "...", "..."],')
    prompt_parts.append('  "hidden_cascades": ["...", "..."],')
    prompt_parts.append('  "misleading_metrics": ["...", "..."],')
    prompt_parts.append('  "recommended_actions": ["action_id", "..."]')
    prompt_parts.append("}")
    prompt_parts.append("```")
    
    return "\n".join(prompt_parts)


def extract_immediate_threats(game_state: GameState) -> List[str]:
    """Extract immediate threats from game state."""
    threats = []
    
    # Check critical resources
    if game_state.world.resources.oxygen_level.current <= game_state.world.resources.oxygen_level.critical_threshold:
        threats.append(f"Oxygen critically low: {game_state.world.resources.oxygen_level.current}%")
    
    if game_state.world.resources.power_level.current <= 20:
        threats.append(f"Power critically low: {game_state.world.resources.power_level.current}%")
    
    # Check ship systems
    if game_state.world.ship_systems.reactor_integrity.current <= 30:
        threats.append(f"Reactor integrity critical: {game_state.world.ship_systems.reactor_integrity.current}%")
    
    if game_state.world.ship_systems.hull_integrity.current <= 25:
        threats.append(f"Hull integrity critical: {game_state.world.ship_systems.hull_integrity.current}%")
    
    # Check crew panic
    if game_state.world.panic_level >= 80:
        threats.append(f"Crew panic level critical: {game_state.world.panic_level}%")
    
    # Check NPC breakdowns
    panicking_npcs = [npc for npc in game_state.npcs.values() if npc.is_in_panic()]
    if panicking_npcs:
        threats.append(f"{len(panicking_npcs)} NPC(s) in panic/breakdown state")
    
    return threats


def extract_medium_term_risks(game_state: GameState) -> List[str]:
    """Extract medium-term risks (1-2 days)."""
    risks = []
    
    # Resource decay
    if game_state.world.resources.oxygen_level.current <= 40:
        risks.append("Oxygen will deplete within 1-2 days if not addressed")
    
    if game_state.world.resources.fuel_reserves.current <= 30:
        risks.append("Fuel reserves running low, may affect escape pods")
    
    # System degradation
    if game_state.world.ship_systems.reactor_integrity.current <= 50:
        risks.append("Reactor integrity declining, risk of critical failure")
    
    # Crew morale
    if game_state.world.crew_morale <= 40:
        risks.append("Low crew morale may lead to mutiny or refusal to cooperate")
    
    return risks


def extract_long_term_concerns(game_state: GameState) -> List[str]:
    """Extract long-term strategic concerns."""
    concerns = []
    
    # Time pressure
    days_left = 7 - game_state.world.day
    if days_left <= 2:
        concerns.append(f"Only {days_left} day(s) remaining - time is running out")
    
    # Resource sustainability
    total_resources = (
        game_state.world.resources.oxygen_level.current +
        game_state.world.resources.food_water.current +
        game_state.world.resources.medical_supplies.current
    ) / 3
    if total_resources <= 40:
        concerns.append("Overall resource levels unsustainable for remaining time")
    
    # Crew cohesion
    if game_state.world.crew_cohesion <= 50:
        concerns.append("Crew cohesion deteriorating - may fragment into factions")
    
    return concerns
