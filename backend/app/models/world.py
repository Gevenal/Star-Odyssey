"""World state model."""

from typing import Dict, List
from pydantic import BaseModel, Field, field_validator
from app.models.resources import ResourceLevels, ShipSystems
from app.models.location import LocationState


class WorldState(BaseModel):
    """Complete world/ship state."""

    day: int = Field(
        default=1,
        ge=1,
        le=7,
        description="Current day (1-7)"
    )
    turn: int = Field(
        default=1,
        ge=1,
        le=12,
        description="Current turn within day (1-12, each turn is 2 hours)"
    )
    time_of_day: str = Field(
        default="00:00",
        description="Current time in 24-hour format",
        pattern=r"^([0-1][0-9]|2[0-3]):[0-5][0-9]$"
    )
    resources: ResourceLevels = Field(
        default_factory=ResourceLevels,
        description="All ship resource levels"
    )
    ship_systems: ShipSystems = Field(
        default_factory=ShipSystems,
        description="All ship system integrity levels"
    )
    location_states: Dict[str, LocationState] = Field(
        default_factory=dict,
        description="Current state of each location (location_id -> state)"
    )
    crew_morale: int = Field(
        default=60,
        ge=0,
        le=100,
        description="Overall crew morale (0-100)"
    )
    crew_cohesion: int = Field(
        default=70,
        ge=0,
        le=100,
        description="How well crew works together (0-100)"
    )
    panic_level: int = Field(
        default=25,
        ge=0,
        le=100,
        description="Overall panic/chaos level (0-100)"
    )
    global_flags: Dict[str, bool] = Field(
        default_factory=dict,
        description="World-level boolean flags for major events",
        examples=[{"reactor_online": True, "distress_signal_sent": False, "hull_breach_sealed": True}]
    )
    events_occurred: List[str] = Field(
        default_factory=list,
        description="Event IDs that have occurred",
        examples=[["event_reactor_failure", "event_crew_conflict"]]
    )
    active_threats: List[str] = Field(
        default_factory=list,
        description="Currently active threats or crises",
        examples=[["oxygen_leak_sector_3", "reactor_overheating", "hull_breach_cargo"]]
    )

    @field_validator("crew_morale", "crew_cohesion", "panic_level")
    @classmethod
    def validate_percentage(cls, v):
        """Ensure percentage values stay in valid range."""
        return max(0, min(100, v))

    @field_validator("day")
    @classmethod
    def validate_day(cls, v):
        """Ensure day stays in valid range."""
        return max(1, min(7, v))

    @field_validator("turn")
    @classmethod
    def validate_turn(cls, v):
        """Ensure turn stays in valid range."""
        return max(1, min(12, v))

    def get_total_turn_count(self) -> int:
        """Calculate total turn count (day * 12 + turn)."""
        return (self.day - 1) * 12 + self.turn

    def is_morale_critical(self) -> bool:
        """Check if morale is critically low."""
        return self.crew_morale <= 25

    def is_cohesion_critical(self) -> bool:
        """Check if cohesion is critically low."""
        return self.crew_cohesion <= 25

    def is_panic_critical(self) -> bool:
        """Check if panic is critically high."""
        return self.panic_level >= 75

    def has_event_occurred(self, event_id: str) -> bool:
        """Check if an event has occurred."""
        return event_id in self.events_occurred

    def has_active_threat(self, threat_id: str) -> bool:
        """Check if a threat is currently active."""
        return threat_id in self.active_threats

    def get_flag(self, flag_name: str, default: bool = False) -> bool:
        """Get a world flag value."""
        return self.global_flags.get(flag_name, default)

    def get_location_state(self, location_id: str) -> LocationState:
        """Get location state, creating default if not exists."""
        if location_id not in self.location_states:
            self.location_states[location_id] = LocationState()
        return self.location_states[location_id]

    def count_critical_resources(self) -> int:
        """Count number of resources in critical state."""
        count = 0
        if self.resources.oxygen_level.is_critical():
            count += 1
        if self.resources.fuel_reserves.is_critical():
            count += 1
        if self.resources.power_level.is_critical():
            count += 1
        if self.resources.medical_supplies.is_critical():
            count += 1
        if self.resources.food_water.is_critical():
            count += 1
        if self.resources.repair_materials.is_critical():
            count += 1
        return count

    class Config:
        json_schema_extra = {
            "example": {
                "day": 2,
                "turn": 5,
                "time_of_day": "08:00",
                "resources": {},
                "ship_systems": {},
                "location_states": {},
                "crew_morale": 55,
                "crew_cohesion": 65,
                "panic_level": 35,
                "global_flags": {
                    "reactor_online": True,
                    "distress_signal_sent": False
                },
                "events_occurred": ["event_initial_wake"],
                "active_threats": ["oxygen_leak_engineering"]
            }
        }
