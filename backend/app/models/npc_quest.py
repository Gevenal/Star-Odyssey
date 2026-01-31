"""NPC quest models."""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class NPCQuest(BaseModel):
    """Quest or request given by an NPC to the player."""

    quest_id: str = Field(
        ...,
        description="Unique quest identifier",
        examples=["quest_repair_reactor", "quest_find_saboteur"]
    )
    npc_id: str = Field(
        ...,
        description="NPC who gave this quest"
    )
    title: str = Field(
        ...,
        description="Quest title",
        examples=["Repair the Reactor", "Find the Saboteur"]
    )
    description: str = Field(
        ...,
        description="Quest description"
    )
    objective: str = Field(
        ...,
        description="What the player needs to do",
        examples=["Repair the reactor to 80%", "Identify who sabotaged the ship"]
    )
    reward: Optional[str] = Field(
        default=None,
        description="Reward description",
        examples=["+20 trust with Captain", "Access to engineering bay"]
    )
    status: str = Field(
        default="active",
        description="Quest status: active, completed, failed, cancelled",
        examples=["active", "completed", "failed"]
    )
    created_at_turn: int = Field(
        ...,
        description="Turn when quest was created"
    )
    completed_at_turn: Optional[int] = Field(
        default=None,
        description="Turn when quest was completed"
    )
    conditions: Dict[str, Any] = Field(
        default_factory=dict,
        description="Conditions for quest completion",
        examples=[{"resource_reactor_level": 80}, {"secret_revealed": "secret_saboteur"}]
    )

    class Config:
        json_schema_extra = {
            "example": {
                "quest_id": "quest_repair_reactor",
                "npc_id": "npc_captain",
                "title": "Repair the Reactor",
                "description": "The reactor is critical. We need it fixed immediately.",
                "objective": "Repair reactor to at least 80%",
                "reward": "+20 trust with Captain, access to bridge controls",
                "status": "active",
                "created_at_turn": 5,
                "conditions": {"resource_reactor_level": 80}
            }
        }
