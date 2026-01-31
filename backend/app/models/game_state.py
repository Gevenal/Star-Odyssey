"""Game state model."""

from typing import Dict, List, Optional
from pydantic import Field
from app.models.base import CamelCaseModel
from app.models.enums import GamePhase, TurnPhase
from app.models.player import PlayerState
from app.models.npc import NPCState
from app.models.world import WorldState


class GameState(CamelCaseModel):
    """Complete game state snapshot."""

    session_id: str = Field(
        ...,
        description="Unique session identifier"
    )
    phase: GamePhase = Field(
        default=GamePhase.INTRO,
        description="Current game phase"
    )
    current_turn_phase: TurnPhase = Field(
        default=TurnPhase.PLAYER_TURN,
        description="Current turn phase"
    )
    player: PlayerState = Field(
        ...,
        description="Player state"
    )
    npcs: Dict[str, NPCState] = Field(
        default_factory=dict,
        description="All NPC states (npc_id -> state)"
    )
    world: WorldState = Field(
        default_factory=WorldState,
        description="World and ship state"
    )
    turn_count: int = Field(
        default=1,
        ge=1,
        description="Total turn count since game start"
    )
    history: List[Dict] = Field(
        default_factory=list,
        description="Turn history (recent actions and events)",
        max_length=50
    )
    oracle_sentience_level: int = Field(
        default=1,
        ge=1,
        le=3,
        description="ORACLE AI awakening level (1=robotic, 2=curious, 3=sentient)"
    )
    ending_triggered: Optional[str] = Field(
        default=None,
        description="Ending ID if game has ended",
        examples=["ending_death", "ending_rescue", "ending_oracle_merge"]
    )

    def get_npc(self, npc_id: str) -> Optional[NPCState]:
        """Get NPC by ID."""
        return self.npcs.get(npc_id)

    def get_alive_npcs(self) -> List[NPCState]:
        """Get all living NPCs."""
        return [npc for npc in self.npcs.values() if npc.alive]

    def get_npcs_at_location(self, location_id: str) -> List[NPCState]:
        """Get all NPCs at a specific location."""
        return [npc for npc in self.npcs.values() if npc.location == location_id and npc.alive]

    def get_npcs_at_player_location(self) -> List[NPCState]:
        """Get all NPCs at player's current location."""
        return self.get_npcs_at_location(self.player.location)

    def is_game_over(self) -> bool:
        """Check if game has ended."""
        return self.ending_triggered is not None or self.phase == GamePhase.ENDING

    def add_to_history(self, entry: Dict):
        """Add entry to history, maintaining max length."""
        self.history.append(entry)
        if len(self.history) > 50:
            self.history = self.history[-50:]

    def count_alive_npcs(self) -> int:
        """Count living NPCs."""
        return sum(1 for npc in self.npcs.values() if npc.alive)

    def get_average_crew_morale(self) -> float:
        """Calculate average morale including NPCs and world state."""
        alive_npcs = self.get_alive_npcs()
        if not alive_npcs:
            return float(self.world.crew_morale)

        # Simple average of world morale and inverse of NPC stress
        npc_morale_avg = sum(100 - npc.stress_level for npc in alive_npcs) / len(alive_npcs)
        return (self.world.crew_morale + npc_morale_avg) / 2

    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "sess_abc123",
                "phase": "playing",
                "current_turn_phase": "player_turn",
                "player": {
                    "name": "Alex Rivera",
                    "health": 85,
                    "stress": 35,
                    "radiation_exposure": 5.0,
                    "location": "bridge",
                    "inventory": ["multi_tool"],
                    "reputation": {"npc_captain": 50},
                    "discovered_secrets": [],
                    "completed_actions": [],
                    "flags": {"met_oracle": True}
                },
                "npcs": {},
                "world": {},
                "turn_count": 15,
                "history": [],
                "oracle_sentience_level": 1,
                "ending_triggered": None
            }
        }
