"""Location models."""

from typing import List, Optional
from pydantic import Field
from app.models.base import CamelCaseModel
from app.models.enums import Atmosphere


class LocationState(CamelCaseModel):
    """Current state of a location."""

    is_sealed: bool = Field(
        default=True,
        description="Whether the location is sealed/pressurized"
    )
    atmosphere: Atmosphere = Field(
        default=Atmosphere.NORMAL,
        description="Current atmospheric condition"
    )
    power_available: bool = Field(
        default=True,
        description="Whether location has power"
    )
    current_hazards: List[str] = Field(
        default_factory=list,
        description="Active hazards in this location",
        examples=[["fire", "radiation_leak", "hull_breach"]]
    )


class Location(CamelCaseModel):
    """Ship location definition."""

    id: str = Field(
        ...,
        description="Unique location identifier",
        examples=["bridge", "engine_room", "med_bay"]
    )
    name: str = Field(
        ...,
        description="Display name of location",
        examples=["Command Bridge", "Engineering Bay"]
    )
    description: str = Field(
        ...,
        description="Detailed location description"
    )
    connected_to: List[str] = Field(
        default_factory=list,
        description="List of directly connected location IDs",
        examples=[["bridge", "crew_quarters", "cargo_bay"]]
    )
    facilities: List[str] = Field(
        default_factory=list,
        description="Available facilities/equipment in this location",
        examples=[["medical_scanner", "repair_station", "oxygen_recycler"]]
    )
    default_npcs: List[str] = Field(
        default_factory=list,
        description="NPCs that start in this location",
        examples=[["npc_chief_engineer", "npc_medic"]]
    )
    current_state: LocationState = Field(
        default_factory=LocationState,
        description="Current state of the location"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "id": "bridge",
                "name": "Command Bridge",
                "description": "The nerve center of Odyssey-7, filled with dormant control stations and emergency lighting.",
                "connected_to": ["crew_quarters", "observation_deck"],
                "facilities": ["navigation_console", "communications_array"],
                "default_npcs": ["npc_captain"],
                "current_state": {
                    "is_sealed": True,
                    "atmosphere": "normal",
                    "power_available": True,
                    "current_hazards": []
                }
            }
        }
