"""Player state model."""

from typing import List, Dict
from pydantic import BaseModel, Field, field_validator


class PlayerState(BaseModel):
    """Complete player state."""

    name: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="Player's chosen name"
    )
    health: int = Field(
        default=100,
        ge=0,
        le=100,
        description="Health percentage (0-100)"
    )
    stress: int = Field(
        default=20,
        ge=0,
        le=100,
        description="Stress level (0-100)"
    )
    radiation_exposure: float = Field(
        default=0.0,
        ge=0.0,
        le=100.0,
        description="Cumulative radiation exposure (0-100)"
    )
    location: str = Field(
        default="cryo_bay",
        description="Current location ID"
    )
    inventory: List[str] = Field(
        default_factory=list,
        description="Item IDs in player inventory",
        examples=[["multi_tool", "medkit", "access_card_engineering"]]
    )
    reputation: Dict[str, int] = Field(
        default_factory=dict,
        description="Reputation with each NPC (npc_id -> reputation score -100 to 100)",
        examples=[{"npc_captain": 50, "npc_engineer": 25, "npc_scientist": -10}]
    )
    discovered_secrets: List[str] = Field(
        default_factory=list,
        description="Secret IDs discovered by player",
        examples=[["secret_saboteur", "secret_hidden_cargo"]]
    )
    completed_actions: List[str] = Field(
        default_factory=list,
        description="Action IDs that have been completed",
        examples=[["repair_life_support", "convince_crew_meeting"]]
    )
    flags: Dict[str, bool] = Field(
        default_factory=dict,
        description="Player-specific boolean flags for quest/story tracking",
        examples=[{"met_oracle": True, "knows_about_sabotage": False, "first_death_witnessed": True}]
    )
    active_quests: List[str] = Field(
        default_factory=list,
        description="Active quest IDs from NPCs",
        examples=[["quest_repair_reactor", "quest_find_saboteur"]]
    )
    completed_quests: List[str] = Field(
        default_factory=list,
        description="Completed quest IDs",
        examples=[["quest_repair_reactor"]]
    )

    @field_validator("health")
    @classmethod
    def validate_health(cls, v):
        """Ensure health stays in valid range."""
        return max(0, min(100, v))

    @field_validator("stress")
    @classmethod
    def validate_stress(cls, v):
        """Ensure stress stays in valid range."""
        return max(0, min(100, v))

    @field_validator("radiation_exposure")
    @classmethod
    def validate_radiation(cls, v):
        """Ensure radiation stays in valid range."""
        return max(0.0, min(100.0, v))

    @field_validator("reputation")
    @classmethod
    def validate_reputation_values(cls, v):
        """Ensure all reputation values are in valid range."""
        return {k: max(-100, min(100, val)) for k, val in v.items()}

    def is_critical_health(self) -> bool:
        """Check if player health is critical."""
        return self.health <= 25

    def is_highly_stressed(self) -> bool:
        """Check if player is highly stressed."""
        return self.stress >= 75

    def is_radiation_critical(self) -> bool:
        """Check if radiation exposure is critical."""
        return self.radiation_exposure >= 75.0

    def has_item(self, item_id: str) -> bool:
        """Check if player has an item."""
        return item_id in self.inventory

    def has_discovered_secret(self, secret_id: str) -> bool:
        """Check if player has discovered a secret."""
        return secret_id in self.discovered_secrets

    def has_completed_action(self, action_id: str) -> bool:
        """Check if player has completed an action."""
        return action_id in self.completed_actions

    def get_flag(self, flag_name: str, default: bool = False) -> bool:
        """Get a player flag value."""
        return self.flags.get(flag_name, default)

    def get_reputation_with(self, npc_id: str) -> int:
        """Get reputation with specific NPC (defaults to 0)."""
        return self.reputation.get(npc_id, 0)

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Alex Rivera",
                "health": 85,
                "stress": 35,
                "radiation_exposure": 5.0,
                "location": "bridge",
                "inventory": ["multi_tool", "medkit"],
                "reputation": {
                    "npc_captain": 60,
                    "npc_engineer": 40,
                    "npc_scientist": 20
                },
                "discovered_secrets": ["secret_oracle_awakening"],
                "completed_actions": ["explore_bridge", "talk_to_captain"],
                "flags": {
                    "met_oracle": True,
                    "first_crisis_resolved": True
                }
            }
        }
