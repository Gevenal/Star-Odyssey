"""Action models."""

from typing import List, Optional, Dict
from pydantic import BaseModel, Field
from app.models.enums import ActionCategory


class PlayerAction(BaseModel):
    """Player action input."""

    session_id: str = Field(
        ...,
        description="Game session identifier"
    )
    action_type: ActionCategory = Field(
        ...,
        description="Category of action"
    )
    action_id: str = Field(
        ...,
        description="Specific action identifier",
        examples=["repair_reactor", "talk_to_engineer", "investigate_breach"]
    )
    action_text: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Player's action description in natural language"
    )
    target_location: Optional[str] = Field(
        default=None,
        description="Target location ID if action involves movement or location"
    )
    target_npc: Optional[str] = Field(
        default=None,
        description="Target NPC ID if action involves NPC interaction"
    )
    target_item: Optional[str] = Field(
        default=None,
        description="Target item ID if action involves item"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "sess_abc123",
                "action_type": "social_interaction",
                "action_id": "talk_to_captain",
                "action_text": "I approach Captain Chen and ask about the ship's status.",
                "target_location": None,
                "target_npc": "npc_captain",
                "target_item": None
            }
        }


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

    id: str = Field(
        ...,
        description="Unique action identifier"
    )
    name: str = Field(
        ...,
        description="Display name of action"
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
        examples=[["successfully repair system", "partial repair", "failure causes damage"]]
    )
    cooldown: int = Field(
        default=0,
        ge=0,
        description="Number of turns before action can be used again (0 = no cooldown)"
    )
    one_time: bool = Field(
        default=False,
        description="Whether action can only be performed once per game"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "id": "repair_life_support",
                "name": "Repair Life Support System",
                "category": "resource_management",
                "description": "Attempt to repair the damaged life support system using available materials.",
                "requirements": {
                    "location": "engineering",
                    "items": ["repair_kit"],
                    "min_resource_levels": {"power_level": 15.0},
                    "time_cost": 2
                },
                "possible_outcomes": [
                    "Full repair restores life support efficiency",
                    "Partial repair improves efficiency",
                    "Repair fails and consumes materials"
                ],
                "cooldown": 5,
                "one_time": False
            }
        }
