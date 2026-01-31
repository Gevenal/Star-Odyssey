"""Generate game endings based on final state."""
from typing import Dict
from app.models.game_state import GameState
from app.ai.gemini_client import GeminiClient
from app.utils.logger import get_logger

logger = get_logger(__name__)


class EndingGenerator:
    """Generates narrative endings based on game state."""

    def __init__(self, gemini_client: GeminiClient):
        self.gemini = gemini_client

    async def generate_ending(self, final_state: GameState) -> dict:
        """Generate ending based on final state."""
        logger.info(f"Generating ending for session {final_state.session_id}")

        metrics = self._analyze_final_state(final_state)
        ending_type = self._determine_ending_type(metrics)
        prompt = self._build_ending_prompt(final_state, metrics, ending_type)

        narration = await self.gemini.generate(prompt)
        survivor_fates = await self._generate_survivor_fates(final_state)
        epilogue = await self._generate_epilogue(final_state, metrics, ending_type)
        title = self._generate_title(ending_type, metrics)

        return {
            "ending_type": ending_type,
            "title": title,
            "narration": narration,
            "survivor_fates": survivor_fates,
            "epilogue": epilogue,
            "statistics": metrics,
        }

    def _analyze_final_state(self, state: GameState) -> dict:
        """Extract key metrics for ending determination."""
        survivors = [npc for npc in state.npcs.values() if npc.alive]
        casualties = [npc for npc in state.npcs.values() if not npc.alive]

        return {
            "survivors": len(survivors),
            "casualties": len(casualties),
            "survivor_list": [npc.name for npc in survivors],
            "casualty_list": [npc.name for npc in casualties],
            "avg_morale": state.world.crew_morale,
            "player_alive": state.player.health > 0,
            "player_health": state.player.health,
            "secrets_found": len(state.player.discovered_secrets),
            "oracle_sentience": state.oracle_sentience_level,
            "days_survived": state.world.day,
            "turns_survived": state.turn_count,
        }

    def _determine_ending_type(self, metrics: dict) -> str:
        """Determine ending type based on metrics."""
        if metrics["player_alive"] and metrics["survivors"] >= 3 and metrics["avg_morale"] >= 50:
            return "victory"

        if not metrics["player_alive"] or metrics["survivors"] == 0:
            return "defeat"

        return "mixed"

    def _build_ending_prompt(self, state: GameState, metrics: dict, ending_type: str) -> str:
        """Build prompt for ending generation."""
        return f"""Generate a dramatic ending narration for a sci-fi survival game.

ENDING TYPE: {ending_type.upper()}

FINAL SITUATION:
- Days Survived: {metrics['days_survived']}
- Player Status: {'ALIVE' if metrics['player_alive'] else 'DECEASED'}
- Crew Survivors: {metrics['survivors']}
- Casualties: {metrics['casualties']}
- Crew Morale: {metrics['avg_morale']}

Write a dramatic ending (300-500 words):"""

    async def _generate_survivor_fates(self, state: GameState) -> Dict[str, str]:
        """Generate individual fate descriptions."""
        fates = {}

        for npc in state.npcs.values():
            if npc.alive:
                fates[npc.id] = f"{npc.name} survived the crisis."
            else:
                fates[npc.id] = f"{npc.name} gave their life for the crew."

        return fates

    async def _generate_epilogue(self, state: GameState, metrics: dict, ending_type: str) -> str:
        """Generate brief epilogue."""
        if ending_type == "victory":
            return f"The {metrics['survivors']} survivors returned home as heroes."
        elif ending_type == "defeat":
            return "The ship drifted into the void, a silent monument."
        else:
            return f"Though {metrics['casualties']} were lost, the survivors carried on."

    def _generate_title(self, ending_type: str, metrics: dict) -> str:
        """Generate ending title."""
        import random

        if ending_type == "victory":
            titles = ["Against All Odds", "The Return", "Triumph in the Void"]
        elif ending_type == "defeat":
            titles = ["Lost in the Stars", "The Final Transmission", "Into the Dark"]
        else:
            titles = ["Pyrrhic Victory", "The Cost of Survival", "What Remains"]

        return random.choice(titles)
