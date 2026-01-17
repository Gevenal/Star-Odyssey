"""Event models."""

from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field
from app.models.response import StateChange


class RandomEvent(BaseModel):
    """Random world event definition."""

    id: str = Field(
        ...,
        description="Unique event identifier",
        examples=["event_reactor_surge", "event_hull_breach", "event_crew_conflict"]
    )
    name: str = Field(
        ...,
        description="Display name of event"
    )
    category: str = Field(
        ...,
        description="Event category",
        examples=["crisis", "opportunity", "character", "mystery"]
    )
    description: str = Field(
        ...,
        description="Event description/narration"
    )
    trigger_conditions: Dict[str, Any] = Field(
        default_factory=dict,
        description="Conditions required for event to trigger",
        examples=[{
            "min_turn": 10,
            "max_turn": 30,
            "required_flags": {"reactor_repaired": True},
            "min_crew_morale": 30
        }]
    )
    effects: List[StateChange] = Field(
        default_factory=list,
        description="Automatic state changes when event occurs"
    )
    player_choices: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="Player choices if event is interactive",
        examples=[[
            {
                "id": "choice_help",
                "text": "Help the injured crew member",
                "outcomes": ["use_medical_supplies", "gain_reputation"]
            },
            {
                "id": "choice_ignore",
                "text": "Prioritize the reactor repair",
                "outcomes": ["lose_reputation", "save_time"]
            }
        ]]
    )
    affected_npcs: List[str] = Field(
        default_factory=list,
        description="NPC IDs affected by this event",
        examples=[["npc_engineer", "npc_medic"]]
    )
    probability: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Probability of event occurring when conditions are met (0.0-1.0)"
    )
    one_time: bool = Field(
        default=True,
        description="Whether event can only occur once"
    )
    cooldown: int = Field(
        default=0,
        ge=0,
        description="Turns before event can occur again (if not one_time)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "id": "event_oxygen_leak",
                "name": "Oxygen Leak Detected",
                "category": "crisis",
                "description": "ORACLE alerts you to a critical oxygen leak in the cargo bay. The atmospheric pressure is dropping rapidly.",
                "trigger_conditions": {
                    "min_turn": 5,
                    "max_turn": 40,
                    "hull_integrity_below": 70.0
                },
                "effects": [
                    {
                        "entity_type": "world",
                        "entity_id": "world",
                        "field": "active_threats",
                        "old_value": [],
                        "new_value": ["oxygen_leak_cargo"],
                        "reason": "oxygen leak event triggered"
                    }
                ],
                "player_choices": [
                    {
                        "id": "immediate_seal",
                        "text": "Immediately seal the cargo bay",
                        "outcomes": ["stop leak quickly", "trap anyone inside"]
                    },
                    {
                        "id": "evacuate_first",
                        "text": "Evacuate crew first, then seal",
                        "outcomes": ["save crew", "lose more oxygen"]
                    }
                ],
                "affected_npcs": ["npc_engineer"],
                "probability": 0.3,
                "one_time": True,
                "cooldown": 0
            }
        }
