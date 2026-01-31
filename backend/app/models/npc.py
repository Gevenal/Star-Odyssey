"""NPC models."""

from typing import List, Dict, Optional
from pydantic import BaseModel, Field, field_validator
from app.models.enums import NPCDisposition


class PersonalityTraits(BaseModel):
    """NPC personality characteristics."""

    core_value: str = Field(
        ...,
        description="Primary driving value",
        examples=["survival", "duty", "knowledge", "family", "revenge"]
    )
    social_style: str = Field(
        ...,
        description="How they interact socially",
        examples=["authoritative", "collaborative", "withdrawn", "manipulative", "empathetic"]
    )
    stress_response: str = Field(
        ...,
        description="How they respond to pressure",
        examples=["aggressive", "analytical", "freezes", "proactive", "denial"]
    )
    decision_making: str = Field(
        ...,
        description="Decision-making approach",
        examples=["logical", "emotional", "impulsive", "cautious", "pragmatic"]
    )
    morality: str = Field(
        ...,
        description="Moral framework",
        examples=["utilitarian", "deontological", "selfish", "selfless", "flexible"]
    )
    quirks: List[str] = Field(
        default_factory=list,
        description="Notable personality quirks or habits",
        examples=[["quotes ancient texts", "counts things obsessively", "hums when nervous"]]
    )
    speech_pattern: Optional[str] = Field(
        default=None,
        description="Speech pattern and communication style",
        examples=["technical_dry", "casual_slang", "stutter_nervous", "cryptic", "formal_precise", "rapid_technical"]
    )

    class Config:
        json_schema_extra = {
            "example": {
                "core_value": "duty",
                "social_style": "authoritative",
                "stress_response": "analytical",
                "decision_making": "logical",
                "morality": "utilitarian",
                "quirks": ["refers to crew by rank", "checks systems compulsively"]
            }
        }


class NPCRelationship(BaseModel):
    """Relationship between NPCs or NPC and player."""

    target_npc_id: str = Field(
        ...,
        description="ID of the other NPC in this relationship"
    )
    trust_level: int = Field(
        default=0,
        ge=-100,
        le=100,
        description="Trust level (-100 to 100, 0 is neutral)"
    )
    relationship_history: List[str] = Field(
        default_factory=list,
        description="Key events that shaped this relationship",
        examples=[["saved my life during hull breach", "disagreed about evacuation priority"]]
    )
    secret_knowledge: List[str] = Field(
        default_factory=list,
        description="Secrets this NPC knows about the target",
        examples=[["knows target sabotaged the ship", "knows target is hiding something"]]
    )
    voice_style: Optional[str] = Field(
        default=None,
        description="How this NPC speaks about/to the target",
        examples=["speaks quickly, uses technical terms to mask anxiety", "formal and distant", "warm and friendly"]
    )

    def get_disposition(self) -> NPCDisposition:
        """Get disposition based on trust level."""
        if self.trust_level >= 75:
            return NPCDisposition.LOYAL
        elif self.trust_level >= 25:
            return NPCDisposition.FRIENDLY
        elif self.trust_level >= -25:
            return NPCDisposition.NEUTRAL
        elif self.trust_level >= -75:
            return NPCDisposition.UNFRIENDLY
        else:
            return NPCDisposition.HOSTILE


class NPCSecret(BaseModel):
    """Secret information about or known by an NPC."""

    id: str = Field(
        ...,
        description="Unique secret identifier",
        examples=["secret_saboteur", "secret_illness", "secret_family"]
    )
    content: str = Field(
        ...,
        description="The secret information"
    )
    known_by_player: bool = Field(
        default=False,
        description="Whether player has discovered this secret"
    )
    reveal_condition: Optional[str] = Field(
        default=None,
        description="Condition or trigger for revealing this secret",
        examples=["trust_level > 50", "medical_scan", "confrontation"]
    )

    class Config:
        json_schema_extra = {
            "example": {
                "id": "secret_saboteur",
                "content": "Secretly sent distress signal that led to ship malfunction",
                "known_by_player": False,
                "reveal_condition": "trust_level > 60 or investigation_complete"
            }
        }


class NPCState(BaseModel):
    """Complete state of an NPC."""

    id: str = Field(
        ...,
        description="Unique NPC identifier",
        examples=["npc_captain", "npc_engineer", "npc_medic"]
    )
    name: str = Field(
        ...,
        description="NPC display name",
        examples=["Captain Chen", "Dr. Voss", "Engineer Malik"]
    )
    role: str = Field(
        ...,
        description="NPC's role or position",
        examples=["Ship Captain", "Chief Medical Officer", "Lead Engineer"]
    )
    location: str = Field(
        ...,
        description="Current location ID"
    )
    alive: bool = Field(
        default=True,
        description="Whether NPC is alive"
    )
    health: int = Field(
        default=100,
        ge=0,
        le=100,
        description="Health percentage (0-100)"
    )
    stress_level: int = Field(
        default=30,
        ge=0,
        le=100,
        description="Stress level (0-100)"
    )
    personality: PersonalityTraits = Field(
        ...,
        description="Personality traits"
    )
    relationships: Dict[str, NPCRelationship] = Field(
        default_factory=dict,
        description="Relationships with other NPCs and player (keyed by entity ID)"
    )
    goals: List[str] = Field(
        default_factory=list,
        description="Current active goals",
        examples=[["repair life support", "convince crew to evacuate", "find the saboteur"]]
    )
    secrets: List[NPCSecret] = Field(
        default_factory=list,
        description="Secrets about or known by this NPC"
    )
    hidden_agenda: Optional[str] = Field(
        default=None,
        description="Hidden agenda or motivation",
        examples=["wants to take command", "protecting someone", "seeking revenge"]
    )
    hidden_agenda_type: Optional[str] = Field(
        default=None,
        description="Type of hidden agenda (from hidden_agendas.json)",
        examples=["corporate_spy", "coward", "whistleblower", "loyalist", "survivor", "protector", "rebel", "researcher"]
    )
    hidden_agenda_conflicts_with_player: bool = Field(
        default=False,
        description="Whether this agenda conflicts with player goals"
    )
    current_activity: Optional[str] = Field(
        default=None,
        description="What the NPC is currently doing",
        examples=["repairing reactor", "sleeping", "arguing with another crew member"]
    )
    inventory: List[str] = Field(
        default_factory=list,
        description="Items the NPC is carrying",
        examples=[["medical_scanner", "trauma_kit"], ["multitool", "repair_kit"], ["captain_keycard", "sidearm"]]
    )
    breaking_point_threshold: Optional[int] = Field(
        default=None,
        ge=0,
        le=100,
        description="Stress level at which NPC breaks down (from template)"
    )
    breakdown_trait: Optional[str] = Field(
        default=None,
        description="Trait that manifests during breakdown"
    )
    breakdown_behavior: Optional[str] = Field(
        default=None,
        description="Description of breakdown behavior"
    )
    is_in_breakdown: bool = Field(
        default=False,
        description="Whether NPC is currently in breakdown state"
    )
    skills: Dict[str, int] = Field(
        default_factory=dict,
        description="NPC skill levels (skill_name -> level 0-100)",
        examples=[{"medical": 75, "engineering": 60, "security": 40}, {"repair": 80, "navigation": 50}]
    )

    @field_validator("health")
    @classmethod
    def validate_health(cls, v):
        """Ensure health stays in valid range."""
        return max(0, min(100, v))

    @field_validator("stress_level")
    @classmethod
    def validate_stress(cls, v):
        """Ensure stress stays in valid range."""
        return max(0, min(100, v))

    def is_critical_health(self) -> bool:
        """Check if NPC health is critical."""
        return self.health <= 25

    def is_highly_stressed(self) -> bool:
        """Check if NPC is highly stressed."""
        return self.stress_level >= 75
    
    def is_in_panic(self) -> bool:
        """Check if NPC has reached breaking point (stress >= threshold)."""
        if self.breaking_point_threshold is None:
            return False
        return self.stress_level >= self.breaking_point_threshold
    
    def update_breakdown_state(self):
        """Update breakdown state based on current stress level."""
        if self.breaking_point_threshold is None:
            self.is_in_breakdown = False
            return
        
        was_in_breakdown = self.is_in_breakdown
        self.is_in_breakdown = self.stress_level >= self.breaking_point_threshold
        
        # If just entered breakdown, log it
        if self.is_in_breakdown and not was_in_breakdown:
            # Breakdown state is now active
            pass
    
    def get_breakdown_behavior_description(self) -> Optional[str]:
        """Get description of breakdown behavior if in breakdown."""
        if not self.is_in_breakdown:
            return None
        return self.breakdown_behavior

    def get_player_disposition(self) -> NPCDisposition:
        """Get NPC's disposition toward player."""
        if "player" in self.relationships:
            return self.relationships["player"].get_disposition()
        return NPCDisposition.NEUTRAL

    class Config:
        json_schema_extra = {
            "example": {
                "id": "npc_captain",
                "name": "Captain Chen",
                "role": "Ship Captain",
                "location": "bridge",
                "alive": True,
                "health": 85,
                "stress_level": 45,
                "personality": {
                    "core_value": "duty",
                    "social_style": "authoritative",
                    "stress_response": "analytical",
                    "decision_making": "logical",
                    "morality": "utilitarian",
                    "quirks": ["refers to crew by rank"]
                },
                "relationships": {
                    "player": {
                        "target_npc_id": "player",
                        "trust_level": 50,
                        "relationship_history": ["woke player from cryo"]
                    }
                },
                "goals": ["restore ship systems", "maintain crew cohesion"],
                "secrets": [],
                "hidden_agenda": None,
                "current_activity": "reviewing system diagnostics"
            }
        }
