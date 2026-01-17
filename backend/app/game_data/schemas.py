"""Pydantic schemas for game data configuration validation."""

from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field
from app.models.enums import Atmosphere, ActionCategory


class GameSettings(BaseModel):
    """Core game settings."""

    max_days: int = Field(default=7, description="Maximum game days")
    turns_per_day: int = Field(default=12, description="Turns per day")
    hours_per_turn: int = Field(default=2, description="Hours per turn")
    starting_location: str = Field(default="command_bridge", description="Starting location ID")


class VictoryCondition(BaseModel):
    """Victory condition definition."""

    id: str = Field(..., description="Condition identifier")
    name: str = Field(..., description="Condition name")
    description: str = Field(..., description="Condition description")
    check_expression: str = Field(
        ...,
        description="Python expression to evaluate",
        examples=["game_state.world.day >= 7 and game_state.player.alive"]
    )


class FailureCondition(BaseModel):
    """Failure condition definition."""

    id: str = Field(..., description="Condition identifier")
    name: str = Field(..., description="Condition name")
    description: str = Field(..., description="Condition description")
    check_expression: str = Field(
        ...,
        description="Python expression to evaluate",
        examples=["game_state.player.health <= 0"]
    )


class LocationConfig(BaseModel):
    """Location configuration."""

    name: str = Field(..., description="Display name")
    description: str = Field(..., description="Location description")
    connected_to: List[str] = Field(
        default_factory=list,
        description="Adjacent location IDs"
    )
    facilities: List[str] = Field(
        default_factory=list,
        description="Available facilities"
    )
    default_atmosphere: Atmosphere = Field(
        default=Atmosphere.NORMAL,
        description="Default atmosphere"
    )
    default_power: bool = Field(default=True, description="Default power state")
    default_sealed: bool = Field(default=True, description="Default sealed state")


class WorldConfig(BaseModel):
    """Complete world configuration."""

    _comment: Optional[str] = Field(None, alias="_comment")
    _version: str = Field(..., alias="_version")
    game_settings: GameSettings = Field(..., description="Game settings")
    victory_conditions: List[VictoryCondition] = Field(
        default_factory=list,
        description="Victory conditions"
    )
    failure_conditions: List[FailureCondition] = Field(
        default_factory=list,
        description="Failure conditions"
    )
    locations: Dict[str, LocationConfig] = Field(
        ...,
        description="Location definitions"
    )


class StateVariableDefinition(BaseModel):
    """State variable configuration."""

    variable_path: str = Field(
        ...,
        description="Dot-notation path",
        examples=["world.resources.oxygen_level.current"]
    )
    display_name: str = Field(..., description="Display name")
    initial_value: Any = Field(..., description="Initial value")
    min_value: Optional[float] = Field(None, description="Minimum value")
    max_value: Optional[float] = Field(None, description="Maximum value")
    critical_threshold: Optional[float] = Field(None, description="Critical threshold")
    decay_rate: float = Field(default=0.0, description="Decay per turn")
    decay_condition: Optional[str] = Field(
        None,
        description="Condition for decay",
        examples=["world.ship_systems.life_support_efficiency.operational"]
    )


class StateVariablesConfig(BaseModel):
    """State variables configuration."""

    _version: str = Field(..., alias="_version")
    variables: List[StateVariableDefinition] = Field(
        ...,
        description="Variable definitions"
    )


class ActionRequirementConfig(BaseModel):
    """Action requirement configuration."""

    location: Optional[str] = Field(None, description="Required location")
    items: List[str] = Field(default_factory=list, description="Required items")
    min_resource_levels: Dict[str, float] = Field(
        default_factory=dict,
        description="Minimum resource levels"
    )
    npc_present: Optional[str] = Field(None, description="Required NPC")
    time_cost: int = Field(default=1, description="Turn cost")
    required_flags: Dict[str, bool] = Field(
        default_factory=dict,
        description="Required flags"
    )


class ActionConfig(BaseModel):
    """Player action configuration."""

    id: str = Field(..., description="Action ID")
    name: str = Field(..., description="Action name")
    category: ActionCategory = Field(..., description="Action category")
    description: str = Field(..., description="Action description")
    requirements: ActionRequirementConfig = Field(
        default_factory=ActionRequirementConfig,
        description="Requirements"
    )
    possible_outcomes: List[str] = Field(
        default_factory=list,
        description="Possible outcomes"
    )
    cooldown: int = Field(default=0, description="Cooldown turns")
    one_time: bool = Field(default=False, description="One-time only")


class EventTriggerCondition(BaseModel):
    """Event trigger condition."""

    min_turn: Optional[int] = Field(None, description="Minimum turn")
    max_turn: Optional[int] = Field(None, description="Maximum turn")
    required_flags: Dict[str, bool] = Field(
        default_factory=dict,
        description="Required flags"
    )
    required_location: Optional[str] = Field(None, description="Required location")
    custom_condition: Optional[str] = Field(
        None,
        description="Custom Python expression"
    )


class EventChoice(BaseModel):
    """Event player choice."""

    id: str = Field(..., description="Choice ID")
    text: str = Field(..., description="Choice text")
    outcomes: List[str] = Field(..., description="Outcome descriptions")


class RandomEventTemplate(BaseModel):
    """Random event template."""

    id: str = Field(..., description="Event ID")
    name: str = Field(..., description="Event name")
    category: str = Field(..., description="Event category")
    description: str = Field(..., description="Event description")
    trigger_conditions: EventTriggerCondition = Field(
        default_factory=EventTriggerCondition,
        description="Trigger conditions"
    )
    player_choices: Optional[List[EventChoice]] = Field(
        None,
        description="Player choices"
    )
    affected_npcs: List[str] = Field(
        default_factory=list,
        description="Affected NPC IDs"
    )
    probability: float = Field(default=1.0, description="Trigger probability")
    one_time: bool = Field(default=True, description="One-time event")


class PersonalityTraitDefinition(BaseModel):
    """Personality trait definition with AI prompt instruction."""

    trait_id: str = Field(..., description="Trait identifier")
    trait_name: str = Field(..., description="Trait name")
    category: str = Field(
        ...,
        description="Trait category",
        examples=["core_value", "social_style", "stress_response"]
    )
    description: str = Field(..., description="Trait description")
    prompt_instruction: str = Field(
        ...,
        description="Instruction for AI to roleplay this trait",
        examples=["You prioritize duty above all else, even personal safety"]
    )
    compatible_with: List[str] = Field(
        default_factory=list,
        description="Compatible trait IDs"
    )
    incompatible_with: List[str] = Field(
        default_factory=list,
        description="Incompatible trait IDs"
    )


class PersonalityTraitsPool(BaseModel):
    """Pool of personality traits."""

    _version: str = Field(..., alias="_version")
    traits: List[PersonalityTraitDefinition] = Field(
        ...,
        description="Trait definitions"
    )


class NPCTemplateConfig(BaseModel):
    """NPC template configuration."""

    template_id: str = Field(..., description="Template ID")
    name: str = Field(..., description="NPC name")
    role: str = Field(..., description="NPC role")
    starting_location: str = Field(..., description="Starting location")
    personality_traits: Dict[str, str] = Field(
        ...,
        description="Personality trait assignments by category"
    )
    starting_health: int = Field(default=100, description="Starting health")
    starting_stress: int = Field(default=30, description="Starting stress")
    initial_goals: List[str] = Field(
        default_factory=list,
        description="Initial goals"
    )
    secrets: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="NPC secrets"
    )
    hidden_agenda: Optional[str] = Field(None, description="Hidden agenda")
    starting_inventory: List[str] = Field(
        default_factory=list,
        description="Starting items"
    )


class AIPromptTemplate(BaseModel):
    """AI prompt template metadata."""

    version: str = Field(..., description="Prompt version")
    compatible_state_versions: List[str] = Field(
        ...,
        description="Compatible state versions",
        examples=[["^1.0", "1.x"]]
    )
    model: str = Field(
        ...,
        description="Target AI model",
        examples=["gemini-pro", "gemini-flash"]
    )
    temperature: float = Field(default=0.8, description="Generation temperature")
    max_tokens: Optional[int] = Field(None, description="Max output tokens")


class AIPromptLibrary(BaseModel):
    """AI prompt library configuration."""

    schema_version: str = Field(..., description="Schema version")
    prompts: Dict[str, AIPromptTemplate] = Field(
        ...,
        description="Prompt templates"
    )


class GameDataBundle(BaseModel):
    """Complete game data bundle."""

    world_config: WorldConfig
    state_variables: StateVariablesConfig
    player_actions: Dict[str, ActionConfig]
    random_events: List[RandomEventTemplate]
    personality_traits: PersonalityTraitsPool
    npc_templates: Dict[str, NPCTemplateConfig]
    ai_prompts: AIPromptLibrary
