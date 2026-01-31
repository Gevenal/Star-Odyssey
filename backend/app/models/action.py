"""Action models."""

from typing import List, Optional, Dict
from pydantic import BaseModel, Field, ConfigDict
from app.models.enums import ActionCategory


def to_camel(string: str) -> str:
    """Convert snake_case to camelCase."""
    components = string.split('_')
    return components[0] + ''.join(x.title() for x in components[1:])


class PlayerAction(BaseModel):
    """Player action input. Accepts both snake_case and camelCase fields."""

    session_id: str = Field(
        ...,
        description="Game session identifier",
        alias="sessionId"
    )
    action_type: ActionCategory = Field(
        ...,
        description="Category of action",
        alias="actionType"
    )
    action_id: str = Field(
        ...,
        description="Specific action identifier",
        examples=["repair_reactor", "talk_to_engineer", "investigate_breach"],
        alias="actionId"
    )
    action_text: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Player's action description in natural language",
        alias="actionText"
    )
    target_location: Optional[str] = Field(
        default=None,
        description="Target location ID if action involves movement or location",
        alias="targetLocation"
    )
    target_npc: Optional[str] = Field(
        default=None,
        description="Target NPC ID if action involves NPC interaction",
        alias="targetNpc"
    )
    target_item: Optional[str] = Field(
        default=None,
        description="Target item ID if action involves item",
        alias="targetItem"
    )

    model_config = ConfigDict(
        populate_by_name=True,  # Accept both alias (camelCase) and field name (snake_case)
        json_schema_extra={
            "example": {
                "sessionId": "sess_abc123",
                "actionType": "social_interaction",
                "actionId": "talk_to_captain",
                "actionText": "I approach Captain Chen and ask about the ship's status.",
                "targetLocation": None,
                "targetNpc": "npc_captain",
                "targetItem": None
            }
        }
    )


class ActionRequirement(BaseModel):
    """Requirements for an action to be available/valid."""

    location: Optional[str] = Field(
        default=None,
        description="Required location ID (None = any location)"
    )
    items: List[str] = Field(
        default_factory=list,
        description="Required item IDs in inventory"
    )
    min_resource_levels: Dict[str, float] = Field(
        default_factory=dict,
        description="Minimum resource levels required (resource_name -> min_value)",
        examples=[{"oxygen_level": 20.0, "power_level": 10.0}]
    )
    npc_present: Optional[str] = Field(
        default=None,
        description="Required NPC ID to be at same location"
    )
    time_cost: int = Field(
        default=1,
        ge=0,
        description="Number of turns this action consumes"
    )
    min_health: Optional[int] = Field(
        default=None,
        ge=0,
        le=100,
        description="Minimum player health required"
    )
    max_stress: Optional[int] = Field(
        default=None,
        ge=0,
        le=100,
        description="Maximum player stress allowed"
    )
    required_flags: Dict[str, bool] = Field(
        default_factory=dict,
        description="Required flag states",
        examples=[{"reactor_repaired": True, "met_oracle": True}]
    )


class ActionDefinition(BaseModel):
    """Definition of a possible action."""
    model_config = ConfigDict(
        populate_by_name=True,
    )

    id: str = Field(
        ...,
        description="Unique action identifier",
        alias="actionId",
        serialization_alias="actionId"
    )
    name: str = Field(
        ...,
        description="Display name of action",
        alias="displayName",
        serialization_alias="displayName"
    )
    category: ActionCategory = Field(
        ...,
        description="Action category"
    )
    description: str = Field(
        ...,
        description="Detailed action description"
    )
    requirements: ActionRequirement = Field(
        default_factory=ActionRequirement,
        description="Requirements to perform this action"
    )
    possible_outcomes: List[str] = Field(
        default_factory=list,
        description="Possible outcome descriptions",
        examples=[["successfully repair system", "partial repair", "failure causes damage"]],
        alias="possibleOutcomes",
        serialization_alias="possibleOutcomes"
    )
    cooldown: int = Field(
        default=0,
        ge=0,
        description="Number of turns before action can be used again (0 = no cooldown)"
    )
    one_time: bool = Field(
        default=False,
        description="Whether action can only be performed once per game",
        alias="oneTime",
        serialization_alias="oneTime"
    )
    # Note: Example moved to model_config above, old class Config removed to avoid conflict
