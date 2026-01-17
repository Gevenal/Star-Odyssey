"""Response models."""

from typing import List, Optional, Any, Literal
from pydantic import BaseModel, Field
from app.models.enums import Mood


class ResourceChange(BaseModel):
    """Represents a change to a resource."""

    resource_name: str = Field(
        ...,
        description="Name of the resource that changed",
        examples=["oxygen_level", "power_level", "medical_supplies"]
    )
    change_amount: float = Field(
        ...,
        description="Amount of change (positive or negative)"
    )
    reason: str = Field(
        ...,
        description="Reason for the change",
        examples=["life support repair", "oxygen leak", "crew consumption"]
    )

    class Config:
        json_schema_extra = {
            "example": {
                "resource_name": "oxygen_level",
                "change_amount": -5.0,
                "reason": "oxygen leak in sector 3"
            }
        }


class StateChange(BaseModel):
    """Represents a change to game state."""

    entity_type: Literal["player", "npc", "world", "location"] = Field(
        ...,
        description="Type of entity that changed"
    )
    entity_id: str = Field(
        ...,
        description="ID of the specific entity",
        examples=["player", "npc_captain", "world", "bridge"]
    )
    field: str = Field(
        ...,
        description="Field that changed",
        examples=["health", "location", "crew_morale", "is_sealed"]
    )
    old_value: Any = Field(
        ...,
        description="Previous value"
    )
    new_value: Any = Field(
        ...,
        description="New value"
    )
    reason: str = Field(
        ...,
        description="Reason for the change"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "entity_type": "player",
                "entity_id": "player",
                "field": "location",
                "old_value": "bridge",
                "new_value": "engineering",
                "reason": "player moved to engineering"
            }
        }


class NPCReaction(BaseModel):
    """NPC reaction to player action."""

    npc_id: str = Field(
        ...,
        description="NPC identifier"
    )
    reaction_text: str = Field(
        ...,
        description="NPC's reaction in natural language"
    )
    disposition_change: int = Field(
        default=0,
        ge=-20,
        le=20,
        description="Change in NPC's disposition toward player (-20 to +20)"
    )
    new_activity: Optional[str] = Field(
        default=None,
        description="New activity the NPC starts doing",
        examples=["follows player", "starts repair work", "retreats to quarters"]
    )

    class Config:
        json_schema_extra = {
            "example": {
                "npc_id": "npc_captain",
                "reaction_text": "Captain Chen nods approvingly. 'Good thinking. We need more people like you.'",
                "disposition_change": 5,
                "new_activity": "coordinates with engineering team"
            }
        }


class GameActionResponse(BaseModel):
    """Response to a player action."""

    success: bool = Field(
        ...,
        description="Whether the action was successful"
    )
    narration: str = Field(
        ...,
        description="AI-generated narrative response to the action"
    )
    resource_changes: List[ResourceChange] = Field(
        default_factory=list,
        description="Resources that changed as result of action"
    )
    state_changes: List[StateChange] = Field(
        default_factory=list,
        description="State changes that occurred"
    )
    npc_reactions: List[NPCReaction] = Field(
        default_factory=list,
        description="NPC reactions to the action"
    )
    available_actions: List[str] = Field(
        default_factory=list,
        description="Action IDs now available to player",
        examples=[["repair_reactor", "talk_to_engineer", "rest"]]
    )
    mood: Mood = Field(
        default=Mood.TENSE,
        description="Current narrative mood"
    )
    trigger_ending: bool = Field(
        default=False,
        description="Whether this action triggered a game ending"
    )
    ending_id: Optional[str] = Field(
        default=None,
        description="Ending identifier if triggered",
        examples=["ending_death", "ending_rescue", "ending_oracle_merge"]
    )
    oracle_message: Optional[str] = Field(
        default=None,
        description="Optional message from ORACLE AI"
    )
    confidence_level: Literal["high", "medium", "speculative"] = Field(
        default="high",
        description="AI confidence in state changes and effects"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "narration": "You carefully approach the damaged life support panel. After diagnostics, you manage to reroute power and restore partial functionality. The air feels slightly fresher already.",
                "resource_changes": [
                    {
                        "resource_name": "repair_materials",
                        "change_amount": -10.0,
                        "reason": "used for life support repair"
                    }
                ],
                "state_changes": [
                    {
                        "entity_type": "world",
                        "entity_id": "world",
                        "field": "ship_systems.life_support_efficiency.integrity",
                        "old_value": 45.0,
                        "new_value": 65.0,
                        "reason": "successful repair"
                    }
                ],
                "npc_reactions": [
                    {
                        "npc_id": "npc_engineer",
                        "reaction_text": "Engineer Malik gives you a rare smile. 'Not bad for a rookie.'",
                        "disposition_change": 8,
                        "new_activity": None
                    }
                ],
                "available_actions": ["talk_to_engineer", "check_reactor", "rest"],
                "mood": "hopeful",
                "trigger_ending": False,
                "ending_id": None,
                "oracle_message": "LIFE SUPPORT EFFICIENCY RESTORED TO 65%. OXYGEN PRODUCTION STABILIZING.",
                "confidence_level": "high"
            }
        }
