"""Resource management rules."""

from typing import Optional

from app.core.rules.base_rule import BaseRule, RuleResult
from app.models.game_state import GameState
from app.models.action import PlayerAction


class ResourceAvailabilityRule(BaseRule):
    """Validates that required resources are available for action."""

    def __init__(self, game_data_loader=None):
        """
        Args:
            game_data_loader: GameDataLoader for action configs. If None, skips checks (valid=True).
        """
        super().__init__()
        self.loader = game_data_loader

    def validate(self, action: PlayerAction, game_state: GameState) -> RuleResult:
        """
        Check if player has sufficient resources and meets requirements to perform action.

        Args:
            action: Player action to validate
            game_state: Current game state

        Returns:
            RuleResult: Valid if location, resources, items, npc_present, required_flags are satisfied.
        """
        if self.loader is None:
            return RuleResult(valid=True)

        action_config = self.loader.get_action(action.action_id)
        if not action_config:
            return RuleResult(valid=True)  # Unknown action_id: allow (e.g. freeform)

        req = action_config.requirements
        resources = game_state.world.resources
        player = game_state.player

        # location: must be at required location
        if req.location is not None and req.location != "":
            if player.location != req.location:
                return RuleResult(
                    valid=False,
                    error=f"Action requires location '{req.location}', you are at '{player.location}'",
                    suggestion=f"Go to {req.location} first",
                )

        # min_resource_levels: each resource must be >= min
        for name, min_val in (req.min_resource_levels or {}).items():
            if not hasattr(resources, name):
                return RuleResult(
                    valid=False,
                    error=f"Unknown resource in action config: {name}",
                )
            r = getattr(resources, name)
            if r.current < min_val:
                return RuleResult(
                    valid=False,
                    error=f"Insufficient {name}: need {min_val}, have {r.current}",
                    suggestion=f"Raise {name} to at least {min_val}",
                )

        # items: all required items in inventory
        for item in (req.items or []):
            if item not in player.inventory:
                return RuleResult(
                    valid=False,
                    error=f"Missing required item: {item}",
                    suggestion=f"Obtain {item} to perform this action",
                )

        # npc_present: required NPC must be at player's location
        if req.npc_present is not None and req.npc_present != "":
            npc_ids = [n.id for n in game_state.get_npcs_at_player_location()]
            if req.npc_present not in npc_ids:
                return RuleResult(
                    valid=False,
                    error=f"Required NPC '{req.npc_present}' is not at your location",
                    suggestion="Find the required NPC or go to their location",
                )

        # required_flags: player.flags must match
        for k, v in (req.required_flags or {}).items():
            if player.flags.get(k) != v:
                return RuleResult(
                    valid=False,
                    error=f"Action requires flag '{k}' to be {v}",
                    suggestion=f"Ensure '{k}' is {v}",
                )

        return RuleResult(valid=True)


class ResourceDecayRule(BaseRule):
    """Applies resource decay each turn."""

    def __init__(self, game_data_loader=None):
        """
        Initialize with game data loader.

        Args:
            game_data_loader: GameDataLoader for state_variables. If None, uses default decay rates.
        """
        super().__init__()
        self.loader = game_data_loader
        self._decay_config = None

    def validate(self, game_state: GameState) -> RuleResult:
        """
        Validate decay can be applied (always true).

        Args:
            game_state: Current game state

        Returns:
            RuleResult: Always valid
        """
        return RuleResult(valid=True)

    def get_decay_config(self) -> dict:
        """
        Load and cache decay configuration from state_variables.json.

        Returns:
            Dict mapping resource names to their decay rates and other config.
        """
        if self._decay_config is not None:
            return self._decay_config

        # Default decay rates if no loader or loading fails
        default_config = {
            "oxygen_level": {"decay_rate": 1.2, "min": 0.0, "max": 100.0, "critical_threshold": 25.0},
            "fuel_reserves": {"decay_rate": 0.8, "min": 0.0, "max": 100.0, "critical_threshold": 15.0},
            "power_level": {"decay_rate": 1.0, "min": 0.0, "max": 100.0, "critical_threshold": 20.0},
            "food_water": {"decay_rate": 0.9, "min": 0.0, "max": 100.0, "critical_threshold": 20.0},
            "medical_supplies": {"decay_rate": 0.0, "min": 0.0, "max": 100.0, "critical_threshold": 15.0},
            "repair_materials": {"decay_rate": 0.0, "min": 0.0, "max": 100.0, "critical_threshold": 10.0},
        }

        if self.loader:
            try:
                state_vars = self.loader.load_state_variables()
                variables = state_vars.get("variables", [])

                for var in variables:
                    # Parse variable_path like "world.resources.oxygen_level.current"
                    path = var.get("variable_path", "")
                    parts = path.split(".")

                    # Extract resource name from path (e.g., "oxygen_level" from "world.resources.oxygen_level.current")
                    if len(parts) >= 3 and parts[0] == "world" and parts[1] == "resources":
                        resource_name = parts[2]
                        default_config[resource_name] = {
                            "decay_rate": var.get("decay_rate", 0.0),
                            "min": var.get("min_value", 0.0),
                            "max": var.get("max_value", 100.0),
                            "critical_threshold": var.get("critical_threshold", 20.0),
                            "decay_condition": var.get("decay_condition"),
                        }
            except Exception:
                pass  # Use default config on error

        self._decay_config = default_config
        return self._decay_config

    def apply_decay(self, game_state: GameState) -> tuple[GameState, dict]:
        """
        Apply resource decay to all resources.

        Args:
            game_state: Current game state

        Returns:
            Tuple of (GameState with decayed resources, dict of changes made)
        """
        decay_config = self.get_decay_config()
        changes = {}
        resources = game_state.world.resources

        for resource_name, config in decay_config.items():
            decay_rate = config.get("decay_rate", 0.0)
            min_value = config.get("min", 0.0)

            if decay_rate <= 0:
                continue  # No decay for this resource

            # Check decay condition if specified
            decay_condition = config.get("decay_condition")
            if decay_condition and not self._check_decay_condition(decay_condition, game_state):
                continue  # Condition not met, skip decay

            # Get current resource value
            resource = getattr(resources, resource_name, None)
            if resource is None:
                continue

            # Handle both object-style (resource.current) and direct values
            if hasattr(resource, 'current'):
                old_value = resource.current
                new_value = max(min_value, old_value - decay_rate)
                resource.current = new_value
            elif isinstance(resource, (int, float)):
                old_value = resource
                new_value = max(min_value, old_value - decay_rate)
                setattr(resources, resource_name, new_value)
            else:
                continue

            if old_value != new_value:
                changes[resource_name] = {
                    "old": old_value,
                    "new": new_value,
                    "decay_rate": decay_rate,
                }

        return game_state, changes

    def _check_decay_condition(self, condition: str, game_state: GameState) -> bool:
        """
        Check if a decay condition is met.

        Args:
            condition: Condition string like "world.ship_systems.life_support_efficiency.operational"
            game_state: Current game state

        Returns:
            True if condition is met (decay should apply), False otherwise.
        """
        if not condition:
            return True

        # Parse condition path
        parts = condition.split(".")

        try:
            # Navigate to the value
            obj = game_state
            for part in parts:
                if hasattr(obj, part):
                    obj = getattr(obj, part)
                elif isinstance(obj, dict) and part in obj:
                    obj = obj[part]
                else:
                    return True  # Condition path invalid, apply decay anyway

            # Check if final value is truthy
            return bool(obj)
        except Exception:
            return True  # On error, apply decay


class CriticalResourceRule(BaseRule):
    """Checks for critically low resources and triggers warnings."""

    def __init__(self, game_data_loader=None):
        """
        Initialize with game data loader.

        Args:
            game_data_loader: GameDataLoader for state_variables. If None, uses default thresholds.
        """
        super().__init__()
        self.loader = game_data_loader
        self._critical_thresholds = None

    def get_critical_thresholds(self) -> dict:
        """
        Load and cache critical thresholds from state_variables.json.

        Returns:
            Dict mapping resource names to their critical thresholds.
        """
        if self._critical_thresholds is not None:
            return self._critical_thresholds

        # Default thresholds if no loader or loading fails
        default_thresholds = {
            "oxygen_level": 25.0,
            "fuel_reserves": 15.0,
            "power_level": 20.0,
            "food_water": 20.0,
            "medical_supplies": 15.0,
            "repair_materials": 10.0,
        }

        if self.loader:
            try:
                state_vars = self.loader.load_state_variables()
                variables = state_vars.get("variables", [])

                for var in variables:
                    path = var.get("variable_path", "")
                    parts = path.split(".")

                    if len(parts) >= 3 and parts[0] == "world" and parts[1] == "resources":
                        resource_name = parts[2]
                        threshold = var.get("critical_threshold")
                        if threshold is not None:
                            default_thresholds[resource_name] = threshold
            except Exception:
                pass

        self._critical_thresholds = default_thresholds
        return self._critical_thresholds

    def validate(self, game_state: GameState) -> RuleResult:
        """
        Check if any resources are at critical levels.

        Args:
            game_state: Current game state

        Returns:
            RuleResult: Valid with metadata about critical resources
        """
        critical_thresholds = self.get_critical_thresholds()
        critical_resources = []
        depleted_resources = []
        warnings = []

        resources = game_state.world.resources

        for resource_name, threshold in critical_thresholds.items():
            resource = getattr(resources, resource_name, None)
            if resource is None:
                continue

            # Get current value
            if hasattr(resource, 'current'):
                current = resource.current
            elif isinstance(resource, (int, float)):
                current = resource
            else:
                continue

            # Check critical status
            if current <= 0:
                depleted_resources.append(resource_name)
                warnings.append(f"CRITICAL: {resource_name.replace('_', ' ').title()} is depleted!")
            elif current <= threshold:
                critical_resources.append(resource_name)
                warnings.append(
                    f"WARNING: {resource_name.replace('_', ' ').title()} is at critical level ({current:.1f})"
                )

        return RuleResult(
            valid=True,
            metadata={
                "critical_resources": critical_resources,
                "depleted_resources": depleted_resources,
                "warnings": warnings,
                "has_critical": len(critical_resources) > 0 or len(depleted_resources) > 0,
            }
        )

    def check_game_over_conditions(self, game_state: GameState) -> tuple[bool, str | None]:
        """
        Check if any resource depletion should trigger game over.

        Args:
            game_state: Current game state

        Returns:
            Tuple of (should_end, ending_id) - ending_id is None if game continues
        """
        resources = game_state.world.resources

        # Check oxygen - instant death if depleted
        oxygen = getattr(resources, 'oxygen_level', None)
        if oxygen is not None:
            current = oxygen.current if hasattr(oxygen, 'current') else oxygen
            if isinstance(current, (int, float)) and current <= 0:
                return True, "ending_oxygen_depletion"

        # Check power - if power is 0, critical systems fail
        power = getattr(resources, 'power_level', None)
        if power is not None:
            current = power.current if hasattr(power, 'current') else power
            if isinstance(current, (int, float)) and current <= 0:
                return True, "ending_power_failure"

        return False, None
