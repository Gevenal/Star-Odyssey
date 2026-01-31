"""API request and response schemas."""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from app.models.game_state import GameState
from app.models.action import ActionDefinition
from app.models.response import GameActionResponse


class GameStartRequest(BaseModel):
    """Request to start a new game."""

    player_name: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="Player's chosen name",
        examples=["Alex Rivera"]
    )
    difficulty: Optional[str] = Field(
        default="normal",
        description="Game difficulty level",
        examples=["easy", "normal", "hard"]
    )
    seed: Optional[int] = Field(
        default=None,
        description="Random seed for reproducible gameplay (optional)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "player_name": "Alex Rivera",
                "difficulty": "normal",
                "seed": None
            }
        }


class GameStartResponse(BaseModel):
    """Response when starting a new game."""

    session_id: str = Field(
        ...,
        description="Unique session identifier for this game"
    )
    opening_narration: str = Field(
        ...,
        description="AI-generated opening narration"
    )
    initial_state: GameState = Field(
        ...,
        description="Initial game state"
    )
    available_actions: List[str] = Field(
        default_factory=list,
        description="Action IDs available at game start",
        examples=[["explore_bridge", "talk_to_oracle", "check_systems"]]
    )
    oracle_message: Optional[str] = Field(
        default=None,
        description="Initial ORACLE message"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "sess_abc123def456",
                "opening_narration": "You wake from cryosleep to flashing red lights and blaring alarms...",
                "initial_state": {},
                "available_actions": ["explore_bridge", "talk_to_oracle"],
                "oracle_message": "ALERT: MULTIPLE SYSTEM FAILURES DETECTED. CREW ASSISTANCE REQUIRED."
            }
        }


class AvailableActionsResponse(BaseModel):
    """Response listing available actions."""

    actions: List[ActionDefinition] = Field(
        default_factory=list,
        description="List of currently available action definitions"
    )
    context_hints: List[str] = Field(
        default_factory=list,
        description="Context-aware hints about what the player might want to do",
        examples=[
            [
                "The reactor is reaching critical temperature",
                "Captain Chen is waiting to speak with you in the bridge",
                "You notice signs of sabotage in the engineering bay"
            ]
        ]
    )
    urgent_actions: List[str] = Field(
        default_factory=list,
        description="Action IDs that are time-sensitive or urgent",
        examples=[["repair_reactor_emergency", "seal_hull_breach"]]
    )

    class Config:
        json_schema_extra = {
            "example": {
                "actions": [],
                "context_hints": [
                    "The oxygen levels are dropping - you should check life support",
                    "Engineer Malik looks like he needs help in the engineering bay"
                ],
                "urgent_actions": ["repair_life_support"]
            }
        }


class TurnEndResponse(BaseModel):
    """Response when ending a turn."""

    events_occurred: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Events that occurred during turn processing"
    )
    npc_actions_taken: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Actions taken by NPCs this turn"
    )
    state_summary: Dict[str, Any] = Field(
        default_factory=dict,
        description="Summary of important state changes"
    )
    narration: str = Field(
        default="",
        description="Narration of what happened during the turn"
    )
    critical_alerts: List[str] = Field(
        default_factory=list,
        description="Critical alerts or warnings",
        examples=[["Oxygen level critical!", "Reactor integrity below 10%!"]]
    )
    turn_number: int = Field(
        ...,
        description="New turn number after advancement"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "events_occurred": [
                    {"event_id": "event_power_surge", "description": "Power surge detected"}
                ],
                "npc_actions_taken": [
                    {"npc_id": "npc_engineer", "action": "repaired power relay"}
                ],
                "state_summary": {
                    "resources_changed": ["oxygen_level: -2", "power_level: +5"],
                    "npcs_moved": ["npc_engineer: bridge -> engineering"]
                },
                "narration": "As time passes, Engineer Malik works tirelessly on the power systems...",
                "critical_alerts": ["Oxygen level approaching critical threshold"],
                "turn_number": 16
            }
        }


class SaveGameRequest(BaseModel):
    """Request to save a game."""

    session_id: str = Field(
        ...,
        description="Session to save"
    )
    save_name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Name for this save"
    )
    description: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Optional save description"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "sess_abc123",
                "save_name": "Day 3 - Before reactor repair",
                "description": "Just discovered the sabotage plot"
            }
        }


class SaveGameResponse(BaseModel):
    """Response when saving a game."""

    save_id: str = Field(
        ...,
        description="Unique save identifier"
    )
    save_name: str = Field(
        ...,
        description="Save name"
    )
    saved_at: str = Field(
        ...,
        description="ISO timestamp of save"
    )
    turn_count: int = Field(
        ...,
        description="Turn number when saved"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "save_id": "save_xyz789",
                "save_name": "Day 3 - Before reactor repair",
                "saved_at": "2024-01-15T14:30:00Z",
                "turn_count": 35
            }
        }


class SaveMetadata(BaseModel):
    """Metadata about a saved game."""

    save_id: str = Field(..., description="Save identifier")
    save_name: str = Field(..., description="Save name")
    description: Optional[str] = Field(None, description="Save description")
    saved_at: str = Field(..., description="ISO timestamp")
    turn_count: int = Field(..., description="Turn number")
    day: int = Field(..., description="Game day")
    player_name: str = Field(..., description="Player name")
    alive_npcs: int = Field(..., description="Number of living NPCs")
    ending_triggered: Optional[str] = Field(None, description="Ending ID if game ended")


class ListSavesResponse(BaseModel):
    """Response listing saved games."""

    saves: List[SaveMetadata] = Field(
        default_factory=list,
        description="List of save metadata"
    )
    total: int = Field(
        ...,
        description="Total number of saves"
    )


class LoadGameResponse(BaseModel):
    """Response when loading a game."""

    session_id: str = Field(
        ...,
        description="New session ID for loaded game"
    )
    game_state: GameState = Field(
        ...,
        description="Loaded game state"
    )
    narration: str = Field(
        ...,
        description="Narration describing the loaded state"
    )
    available_actions: List[str] = Field(
        default_factory=list,
        description="Available action IDs"
    )


class DebugStateResponse(BaseModel):
    """Debug response with full state dump."""

    session_id: str = Field(..., description="Session ID")
    game_state: GameState = Field(..., description="Complete game state")
    internal_flags: Dict[str, Any] = Field(
        default_factory=dict,
        description="Internal system flags and metadata"
    )
    ai_context_size: int = Field(
        ...,
        description="Size of AI context in tokens"
    )
    cache_status: Dict[str, Any] = Field(
        default_factory=dict,
        description="Redis cache status"
    )


class DebugSetVariableRequest(BaseModel):
    """Request to set a state variable for debugging."""

    session_id: str = Field(..., description="Session ID")
    variable_path: str = Field(
        ...,
        description="Dot-notation path to variable",
        examples=["player.health", "world.resources.oxygen_level.current", "npcs.npc_captain.stress_level"]
    )
    value: Any = Field(..., description="Value to set")


class DebugTriggerEventRequest(BaseModel):
    """Request to force trigger an event."""

    session_id: str = Field(..., description="Session ID")
    event_id: str = Field(
        ...,
        description="Event ID to trigger",
        examples=["event_reactor_failure", "event_hull_breach"]
    )
    skip_conditions: bool = Field(
        default=False,
        description="Skip trigger condition checks"
    )


class DebugExplainRisksResponse(BaseModel):
    """AI explanation of current risks."""

    session_id: str = Field(..., description="Session ID")
    risk_analysis: str = Field(
        ...,
        description="AI-generated analysis of current risks and dangers"
    )
    immediate_threats: List[str] = Field(
        default_factory=list,
        description="List of immediate threats"
    )
    medium_term_risks: List[str] = Field(
        default_factory=list,
        description="Medium-term risks (1-2 days)"
    )
    long_term_concerns: List[str] = Field(
        default_factory=list,
        description="Long-term strategic concerns"
    )
    recommended_actions: List[str] = Field(
        default_factory=list,
        description="AI-recommended action IDs"
    )


class NPCTalkRequest(BaseModel):
    """Request to talk to an NPC."""

    session_id: str = Field(
        ...,
        description="Game session ID"
    )
    message: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Player's message to the NPC",
        examples=["What's the status of the reactor?"]
    )

    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "sess_abc123",
                "message": "What's the status of the reactor?"
            }
        }


class NPCTalkResponse(BaseModel):
    """Response from NPC dialogue."""

    npc_id: str = Field(
        ...,
        description="NPC identifier"
    )
    npc_name: str = Field(
        ...,
        description="NPC's name"
    )
    dialogue: str = Field(
        ...,
        description="NPC's response dialogue"
    )
    relationship_level: int = Field(
        ...,
        description="Current trust/relationship level with player (-100 to 100)"
    )
    disposition: str = Field(
        ...,
        description="NPC's disposition toward player",
        examples=["friendly", "neutral", "hostile"]
    )

    class Config:
        json_schema_extra = {
            "example": {
                "npc_id": "npc_captain",
                "npc_name": "Captain Elena Chen",
                "dialogue": "The reactor is stable for now, but we need to keep monitoring it closely.",
                "relationship_level": 50,
                "disposition": "friendly"
            }
        }
