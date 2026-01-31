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
    quest_given: Optional[str] = Field(
        default=None,
        description="Quest ID if NPC gave a quest during dialogue"
    )
    secrets_revealed: List[str] = Field(
        default_factory=list,
        description="Secret IDs revealed during dialogue"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "npc_id": "npc_captain",
                "npc_name": "Captain Elena Chen",
                "dialogue": "The reactor is stable for now, but we need to keep monitoring it closely.",
                "relationship_level": 50,
                "disposition": "friendly",
                "quest_given": None
            }
        }


class NPCInterrogationRequest(BaseModel):
    """Request to interrogate an NPC."""

    session_id: str = Field(..., description="Current game session ID")
    npc_id: str = Field(..., description="NPC to interrogate")
    question: str = Field(..., min_length=1, description="Question to ask")
    interrogation_type: str = Field(
        default="questioning",
        description="Type of interrogation",
        examples=["questioning", "threatening", "confronting"]
    )

    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "sess_abc123",
                "npc_id": "npc_captain",
                "question": "What really happened to the ship?",
                "interrogation_type": "confronting"
            }
        }


class NPCInterrogationResponse(BaseModel):
    """Response from NPC interrogation."""

    npc_id: str = Field(..., description="NPC identifier")
    npc_name: str = Field(..., description="NPC's name")
    response: str = Field(..., description="NPC's response under interrogation")
    trust_change: int = Field(..., description="Change in trust level (usually negative)")
    secrets_revealed: List[str] = Field(
        default_factory=list,
        description="Secret IDs revealed during interrogation"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "npc_id": "npc_captain",
                "npc_name": "Captain Elena Chen",
                "response": "I... I didn't want to tell anyone, but...",
                "trust_change": -10,
                "secrets_revealed": ["secret_captain_override"]
            }
        }


class NPCItemTransferRequest(BaseModel):
    """Request to transfer item with NPC."""

    session_id: str = Field(..., description="Current game session ID")
    npc_id: str = Field(..., description="NPC to interact with")
    item_id: str = Field(..., description="Item ID")
    direction: str = Field(
        ...,
        description="Transfer direction: 'npc_to_player' or 'player_to_npc'",
        examples=["npc_to_player", "player_to_npc"]
    )
    reason: Optional[str] = Field(
        default=None,
        description="Reason for transfer"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "sess_abc123",
                "npc_id": "npc_engineer",
                "item_id": "multitool",
                "direction": "npc_to_player",
                "reason": "gift"
            }
        }


class NPCItemTransferResponse(BaseModel):
    """Response from item transfer."""

    success: bool = Field(..., description="Whether transfer succeeded")
    item_id: str = Field(..., description="Item ID")
    direction: str = Field(..., description="Transfer direction")
    trust_change: int = Field(..., description="Change in trust level")
    message: str = Field(..., description="Result message")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "item_id": "multitool",
                "direction": "npc_to_player",
                "trust_change": 5,
                "message": "Engineer gave you multitool"
            }
        }


class AssignTaskRequest(BaseModel):
    """Request to assign task to NPC."""

    session_id: str = Field(..., description="Current game session ID")
    npc_id: str = Field(..., description="NPC to assign task to")
    task_description: str = Field(..., min_length=1, description="Description of the task")
    task_type: str = Field(
        default="general",
        description="Type of task",
        examples=["repair", "medical", "investigation", "security", "general"]
    )

    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "sess_abc123",
                "npc_id": "npc_engineer",
                "task_description": "Repair the reactor cooling system",
                "task_type": "repair"
            }
        }


class AssignTaskResponse(BaseModel):
    """Response from task assignment."""

    success: bool = Field(..., description="Whether assignment succeeded")
    npc_id: str = Field(..., description="NPC ID")
    npc_name: str = Field(..., description="NPC name")
    task_description: str = Field(..., description="Task description")
    trust_change: int = Field(..., description="Change in trust level")
    message: str = Field(..., description="Result message")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "npc_id": "npc_engineer",
                "npc_name": "Marcus Okafor",
                "task_description": "Repair the reactor cooling system",
                "trust_change": 3,
                "message": "Marcus Okafor accepted the task: Repair the reactor cooling system"
            }
        }


class MediateConflictRequest(BaseModel):
    """Request to mediate conflict between NPCs."""

    session_id: str = Field(..., description="Current game session ID")
    npc1_id: str = Field(..., description="First NPC in conflict")
    npc2_id: str = Field(..., description="Second NPC in conflict")
    mediation_approach: str = Field(
        default="diplomatic",
        description="Approach to mediation",
        examples=["diplomatic", "authoritative", "compromise"]
    )

    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "sess_abc123",
                "npc1_id": "npc_captain",
                "npc2_id": "npc_engineer",
                "mediation_approach": "diplomatic"
            }
        }


class MediateConflictResponse(BaseModel):
    """Response from conflict mediation."""

    success: bool = Field(..., description="Whether mediation succeeded")
    npc1_id: str = Field(..., description="First NPC ID")
    npc2_id: str = Field(..., description="Second NPC ID")
    trust_improvement: Optional[int] = Field(default=None, description="Trust improvement between NPCs")
    morale_boost: Optional[int] = Field(default=None, description="Morale boost from successful mediation")
    message: str = Field(..., description="Result message")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "npc1_id": "npc_captain",
                "npc2_id": "npc_engineer",
                "trust_improvement": 10,
                "morale_boost": 5,
                "message": "Successfully mediated conflict between Captain Chen and Engineer Okafor"
            }
        }


class BoostMoraleRequest(BaseModel):
    """Request to boost crew morale."""

    session_id: str = Field(..., description="Current game session ID")
    boost_method: str = Field(
        default="speech",
        description="Method of boosting morale",
        examples=["speech", "action", "resource_sharing", "celebration"]
    )
    target_npcs: Optional[List[str]] = Field(
        default=None,
        description="Optional list of NPC IDs to target (None = all NPCs)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "sess_abc123",
                "boost_method": "speech",
                "target_npcs": None
            }
        }


class BoostMoraleResponse(BaseModel):
    """Response from morale boost."""

    success: bool = Field(..., description="Whether boost succeeded")
    initial_morale: int = Field(..., description="Initial morale level")
    new_morale: int = Field(..., description="New morale level")
    morale_boost: int = Field(..., description="Amount of morale boosted")
    affected_npcs: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="NPCs affected by morale boost"
    )
    message: str = Field(..., description="Result message")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "initial_morale": 45,
                "new_morale": 55,
                "morale_boost": 10,
                "affected_npcs": [],
                "message": "Morale boosted from 45 to 55 using speech"
            }
        }


class FormAllianceRequest(BaseModel):
    """Request to form alliance with NPC."""

    session_id: str = Field(..., description="Current game session ID")
    npc_id: str = Field(..., description="NPC to form alliance with")
    alliance_type: str = Field(
        default="mutual_support",
        description="Type of alliance",
        examples=["mutual_support", "strategic", "loyalty_pact"]
    )

    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "sess_abc123",
                "npc_id": "npc_captain",
                "alliance_type": "mutual_support"
            }
        }


class FormAllianceResponse(BaseModel):
    """Response from alliance formation."""

    success: bool = Field(..., description="Whether alliance formation succeeded")
    npc_id: str = Field(..., description="NPC ID")
    npc_name: str = Field(..., description="NPC name")
    alliance_type: str = Field(..., description="Type of alliance formed")
    trust_boost: int = Field(..., description="Trust boost from alliance")
    new_trust_level: int = Field(..., description="New trust level")
    message: str = Field(..., description="Result message")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "npc_id": "npc_captain",
                "npc_name": "Captain Elena Chen",
                "alliance_type": "mutual_support",
                "trust_boost": 20,
                "new_trust_level": 75,
                "message": "Formed mutual_support alliance with Captain Elena Chen"
            }
        }


class ListConflictsResponse(BaseModel):
    """Response listing active conflicts."""

    conflicts: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="List of active conflicts between NPCs"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "conflicts": [
                    {
                        "npc1_id": "npc_captain",
                        "npc1_name": "Captain Chen",
                        "npc2_id": "npc_engineer",
                        "npc2_name": "Engineer Okafor",
                        "severity": 3,
                        "description": "Intense conflict between Captain Chen and Engineer Okafor"
                    }
                ]
            }
        }


class ProvideTherapyRequest(BaseModel):
    """Request to provide therapy to NPC."""

    session_id: str = Field(..., description="Current game session ID")
    therapy_type: str = Field(
        default="counseling",
        description="Type of therapy",
        examples=["counseling", "medical", "rest", "forced_rest"]
    )

    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "sess_abc123",
                "therapy_type": "counseling"
            }
        }


class ProvideTherapyResponse(BaseModel):
    """Response from therapy provision."""

    success: bool = Field(..., description="Whether therapy succeeded")
    therapist_name: str = Field(..., description="Therapist NPC name")
    patient_name: str = Field(..., description="Patient NPC name")
    stress_reduction: int = Field(..., description="Stress reduction amount")
    recovered_from_breakdown: bool = Field(..., description="Whether NPC recovered from breakdown")
    morale_boost: int = Field(..., description="Morale boost from recovery")
    message: str = Field(..., description="Result message")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "therapist_name": "Dr. Sarah Chen",
                "patient_name": "Engineer Marcus",
                "stress_reduction": 15,
                "recovered_from_breakdown": True,
                "morale_boost": 3,
                "message": "Dr. Sarah Chen provided counseling to Engineer Marcus. Stress reduced by 15."
            }
        }


class PlayerCounselingRequest(BaseModel):
    """Request for player to provide counseling."""

    session_id: str = Field(..., description="Current game session ID")
    npc_id: str = Field(..., description="NPC to counsel")
    counseling_approach: str = Field(
        default="supportive",
        description="Counseling approach",
        examples=["supportive", "directive", "empathetic"]
    )

    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "sess_abc123",
                "npc_id": "npc_engineer",
                "counseling_approach": "empathetic"
            }
        }


class PlayerCounselingResponse(BaseModel):
    """Response from player counseling."""

    success: bool = Field(..., description="Whether counseling succeeded")
    npc_name: str = Field(..., description="NPC name")
    stress_reduction: int = Field(..., description="Stress reduction amount")
    recovered_from_breakdown: bool = Field(..., description="Whether NPC recovered")
    trust_increase: int = Field(..., description="Trust increase")
    message: str = Field(..., description="Result message")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "npc_name": "Engineer Marcus",
                "stress_reduction": 15,
                "recovered_from_breakdown": True,
                "trust_increase": 10,
                "message": "Provided empathetic counseling to Engineer Marcus. Stress reduced by 15."
            }
        }


class InvestigateNPCRequest(BaseModel):
    """Request to investigate NPC."""

    session_id: str = Field(..., description="Current game session ID")
    npc_id: str = Field(..., description="NPC to investigate")
    investigation_type: str = Field(
        default="background",
        description="Type of investigation",
        examples=["background", "suspicious_behavior", "hidden_agenda", "secrets"]
    )
    investigation_method: str = Field(
        default="questioning",
        description="Investigation method",
        examples=["questioning", "observation", "records_check", "confrontation"]
    )

    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "sess_abc123",
                "npc_id": "npc_engineer",
                "investigation_type": "suspicious_behavior",
                "investigation_method": "observation"
            }
        }


class InvestigateNPCResponse(BaseModel):
    """Response from NPC investigation."""

    success: bool = Field(..., description="Whether investigation succeeded")
    npc_name: str = Field(..., description="NPC name")
    findings: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Investigation findings"
    )
    trust_change: int = Field(..., description="Trust change from investigation")
    message: str = Field(..., description="Result message")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "npc_name": "Engineer Marcus",
                "findings": [
                    {
                        "type": "suspicious_behavior",
                        "description": "Suspicious indicators: extremely high stress levels",
                        "confidence": "medium"
                    }
                ],
                "trust_change": -3,
                "message": "Investigation of Engineer Marcus revealed 1 findings"
            }
        }


class ListSuspiciousNPCsResponse(BaseModel):
    """Response listing suspicious NPCs."""

    suspicious_npcs: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="List of suspicious NPCs with indicators"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "suspicious_npcs": [
                    {
                        "npc_id": "npc_engineer",
                        "npc_name": "Engineer Marcus",
                        "suspicious_score": 5,
                        "indicators": ["extremely high stress", "breakdown behavior"]
                    }
                ]
            }
        }


class GetNPCSkillsResponse(BaseModel):
    """Response with NPC skills."""

    npc_id: str = Field(..., description="NPC ID")
    npc_name: str = Field(..., description="NPC name")
    skills: Dict[str, int] = Field(..., description="Skill levels")
    primary_skills: List[str] = Field(..., description="Primary skills (top 3)")
    average_skill_level: float = Field(..., description="Average skill level")

    class Config:
        json_schema_extra = {
            "example": {
                "npc_id": "npc_engineer",
                "npc_name": "Engineer Marcus",
                "skills": {"engineering": 75, "repair": 80, "science": 45},
                "primary_skills": ["repair", "engineering"],
                "average_skill_level": 66.67
            }
        }
