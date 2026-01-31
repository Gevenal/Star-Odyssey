"""Resource and ship system models."""

from pydantic import Field, field_validator
from app.models.base import CamelCaseModel


class ResourceLevel(CamelCaseModel):
    """Individual resource level tracking."""

    current: float = Field(
        ...,
        ge=0.0,
        description="Current resource level"
    )
    max: float = Field(
        default=100.0,
        gt=0.0,
        description="Maximum resource capacity"
    )
    min: float = Field(
        default=0.0,
        ge=0.0,
        description="Minimum resource level"
    )
    critical_threshold: float = Field(
        default=20.0,
        ge=0.0,
        description="Level below which resource is critical"
    )
    decay_rate: float = Field(
        default=0.0,
        ge=0.0,
        description="Rate of decay per turn"
    )

    @field_validator("current")
    @classmethod
    def validate_current_in_bounds(cls, v, info):
        """Ensure current is between min and max."""
        if "max" in info.data and v > info.data["max"]:
            return info.data["max"]
        if "min" in info.data and v < info.data["min"]:
            return info.data["min"]
        return v

    def is_critical(self) -> bool:
        """Check if resource is at critical level."""
        return self.current <= self.critical_threshold

    def percentage(self) -> float:
        """Get resource level as percentage."""
        if self.max == 0:
            return 0.0
        return (self.current / self.max) * 100.0


class ResourceLevels(CamelCaseModel):
    """All ship resource levels."""

    oxygen_level: ResourceLevel = Field(
        default_factory=lambda: ResourceLevel(
            current=85.0,
            max=100.0,
            critical_threshold=25.0,
            decay_rate=1.2
        ),
        description="Ship oxygen reserves"
    )
    fuel_reserves: ResourceLevel = Field(
        default_factory=lambda: ResourceLevel(
            current=60.0,
            max=100.0,
            critical_threshold=15.0,
            decay_rate=0.8
        ),
        description="Fuel for reactor and thrusters"
    )
    power_level: ResourceLevel = Field(
        default_factory=lambda: ResourceLevel(
            current=75.0,
            max=100.0,
            critical_threshold=20.0,
            decay_rate=1.0
        ),
        description="Available electrical power"
    )
    medical_supplies: ResourceLevel = Field(
        default_factory=lambda: ResourceLevel(
            current=50.0,
            max=100.0,
            critical_threshold=15.0,
            decay_rate=0.0
        ),
        description="Medical supplies and pharmaceuticals"
    )
    food_water: ResourceLevel = Field(
        default_factory=lambda: ResourceLevel(
            current=70.0,
            max=100.0,
            critical_threshold=20.0,
            decay_rate=0.9
        ),
        description="Food and water supplies"
    )
    repair_materials: ResourceLevel = Field(
        default_factory=lambda: ResourceLevel(
            current=40.0,
            max=100.0,
            critical_threshold=10.0,
            decay_rate=0.0
        ),
        description="Materials for ship repairs"
    )


class SystemIntegrity(CamelCaseModel):
    """Individual ship system integrity."""

    integrity: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="System integrity percentage (0-100)"
    )
    operational: bool = Field(
        default=True,
        description="Whether system is currently operational"
    )
    degradation_rate: float = Field(
        default=0.0,
        ge=0.0,
        description="Rate of degradation per turn"
    )

    def is_critical(self) -> bool:
        """Check if system is in critical condition."""
        return self.integrity <= 25.0

    def is_failing(self) -> bool:
        """Check if system is failing."""
        return self.integrity <= 10.0 or not self.operational


class ShipSystems(CamelCaseModel):
    """All ship system integrity levels."""

    reactor_integrity: SystemIntegrity = Field(
        default_factory=lambda: SystemIntegrity(
            integrity=80.0,
            operational=True,
            degradation_rate=0.5
        ),
        description="Nuclear reactor status"
    )
    hull_integrity: SystemIntegrity = Field(
        default_factory=lambda: SystemIntegrity(
            integrity=65.0,
            operational=True,
            degradation_rate=0.3
        ),
        description="Ship hull structural integrity"
    )
    life_support_efficiency: SystemIntegrity = Field(
        default_factory=lambda: SystemIntegrity(
            integrity=75.0,
            operational=True,
            degradation_rate=0.7
        ),
        description="Life support system efficiency"
    )
    navigation_systems: SystemIntegrity = Field(
        default_factory=lambda: SystemIntegrity(
            integrity=55.0,
            operational=True,
            degradation_rate=0.2
        ),
        description="Navigation and guidance systems"
    )
    communications_array: SystemIntegrity = Field(
        default_factory=lambda: SystemIntegrity(
            integrity=30.0,
            operational=False,
            degradation_rate=0.0
        ),
        description="Long-range communication systems"
    )
    escape_pods_ready: int = Field(
        default=6,
        ge=0,
        le=8,
        description="Number of functional escape pods (0-8)"
    )

    def critical_systems_count(self) -> int:
        """Count number of systems in critical condition."""
        count = 0
        if self.reactor_integrity.is_critical():
            count += 1
        if self.hull_integrity.is_critical():
            count += 1
        if self.life_support_efficiency.is_critical():
            count += 1
        if self.navigation_systems.is_critical():
            count += 1
        if self.communications_array.is_critical():
            count += 1
        return count
