"""Location and movement rules."""

from app.core.rules.base_rule import BaseRule, RuleResult
from app.models.game_state import GameState
from app.models.action import PlayerAction
from app.models.enums import Atmosphere


class LocationTopologyRule(BaseRule):
    """Validates movement between connected locations."""

    def __init__(self, game_data_loader):
        """
        Initialize with game data loader.

        Args:
            game_data_loader: GameDataLoader instance for location data
        """
        super().__init__()
        self.data = game_data_loader

    def validate(self, action: PlayerAction, game_state: GameState) -> RuleResult:
        """
        Check if target location is adjacent to current location.

        Args:
            action: Player action (must have target_location)
            game_state: Current game state

        Returns:
            RuleResult: Valid if locations are connected
        """
        if not action.target_location:
            return RuleResult(valid=True)  # No movement, no validation needed

        if self.data is None:
            return RuleResult(valid=True)  # No loader: skip (fail open)

        current_location = game_state.player.location
        target_location = action.target_location

        try:
            world_config = self.data.load_world_config()
        except Exception:
            return RuleResult(valid=True)  # Load error: skip

        current_loc_config = world_config.locations.get(current_location)
        if not current_loc_config:
            return RuleResult(
                valid=False,
                error=f"Unknown current location: {current_location}",
                suggestion="Check your current location",
            )

        if target_location not in current_loc_config.connected_to:
            available = ", ".join(current_loc_config.connected_to) if current_loc_config.connected_to else "(none)"
            return RuleResult(
                valid=False,
                error=f"Cannot reach {target_location} from {current_location}",
                suggestion=f"Available from here: {available}",
            )

        return RuleResult(valid=True)


class AtmosphereAccessRule(BaseRule):
    """Validates player can safely access location based on atmosphere."""

    def __init__(self, game_data_loader=None):
        """
        Initialize with optional game data loader.

        Args:
            game_data_loader: GameDataLoader for world config. If None, skips checks.
        """
        super().__init__()
        self.loader = game_data_loader

    def validate(self, action: PlayerAction, game_state: GameState) -> RuleResult:
        """
        Check if target location has safe atmosphere.

        Args:
            action: Player action with target_location
            game_state: Current game state

        Returns:
            RuleResult: Valid if atmosphere is safe or player has protection
        """
        if not action.target_location:
            return RuleResult(valid=True)

        target_location = action.target_location
        player_inventory = game_state.player.inventory or []

        # Get location atmosphere from game state or world config
        atmosphere = self._get_location_atmosphere(target_location, game_state)

        if atmosphere == Atmosphere.VACUUM or atmosphere == "vacuum":
            has_suit = "space_suit" in player_inventory or "eva_suit" in player_inventory
            if not has_suit:
                return RuleResult(
                    valid=False,
                    error=f"Cannot enter {target_location} - vacuum conditions require space suit",
                    suggestion="Find a space suit or EVA suit before entering"
                )

        if atmosphere == Atmosphere.TOXIC or atmosphere == "toxic":
            has_mask = "gas_mask" in player_inventory or "hazmat_suit" in player_inventory
            if not has_mask:
                return RuleResult(
                    valid=False,
                    error=f"Cannot enter {target_location} - toxic atmosphere detected",
                    suggestion="Obtain a gas mask or hazmat suit first"
                )

        if atmosphere == Atmosphere.LOW_OXYGEN or atmosphere == "low_oxygen":
            # Allow but warn - player will take damage over time
            return RuleResult(
                valid=True,
                suggestion=f"Warning: Low oxygen in {target_location}. Extended stay may be dangerous."
            )

        return RuleResult(valid=True)

    def _get_location_atmosphere(self, location_id: str, game_state: GameState) -> str:
        """
        Get atmosphere type for a location.

        First checks dynamic game state, then falls back to world config defaults.
        """
        # Check dynamic state first (location may have changed atmosphere)
        if hasattr(game_state.world, 'locations') and game_state.world.locations:
            location_state = game_state.world.locations.get(location_id)
            if location_state and hasattr(location_state, 'atmosphere'):
                return location_state.atmosphere

        # Fall back to world config defaults
        if self.loader:
            try:
                world_config = self.loader.load_world_config()
                location_config = world_config.locations.get(location_id)
                if location_config and hasattr(location_config, 'default_atmosphere'):
                    return location_config.default_atmosphere
            except Exception:
                pass

        # Default to normal atmosphere
        return "normal"

    def get_priority(self) -> int:
        """Check atmosphere after topology but before seals."""
        return 5


class LocationSealRule(BaseRule):
    """Validates location is not sealed/locked."""

    def __init__(self, game_data_loader=None):
        """
        Initialize with optional game data loader.

        Args:
            game_data_loader: GameDataLoader for world config. If None, skips checks.
        """
        super().__init__()
        self.loader = game_data_loader

    def validate(self, action: PlayerAction, game_state: GameState) -> RuleResult:
        """
        Check if location is sealed and player has access.

        Args:
            action: Player action with target_location
            game_state: Current game state

        Returns:
            RuleResult: Valid if location is accessible
        """
        if not action.target_location:
            return RuleResult(valid=True)

        target_location = action.target_location
        player_inventory = game_state.player.inventory or []
        player_flags = game_state.player.flags or {}

        # Check if location is currently sealed
        is_sealed = self._is_location_sealed(target_location, game_state)

        if not is_sealed:
            # Location is open
            return RuleResult(valid=True)

        # Location is sealed - check if player has access

        # Check for location-specific access card
        required_card = f"access_card_{target_location}"
        if required_card in player_inventory:
            return RuleResult(valid=True)

        # Check for captain override keycard
        if "captain_keycard" in player_inventory:
            return RuleResult(valid=True)

        # Check for master access flag (e.g., from hacking or story event)
        if player_flags.get(f"access_granted_{target_location}"):
            return RuleResult(valid=True)

        # Check for security override flag
        if player_flags.get("security_override_active"):
            return RuleResult(valid=True)

        # Location is sealed and player lacks access
        location_name = self._get_location_name(target_location)
        return RuleResult(
            valid=False,
            error=f"{location_name} is sealed - access restricted",
            suggestion=f"Find {required_card} or obtain captain's keycard for override"
        )

    def _is_location_sealed(self, location_id: str, game_state: GameState) -> bool:
        """
        Check if a location is currently sealed.

        First checks dynamic game state, then falls back to world config defaults.
        """
        # Check dynamic state first (seal status may have changed during gameplay)
        if hasattr(game_state.world, 'locations') and game_state.world.locations:
            location_state = game_state.world.locations.get(location_id)
            if location_state:
                if hasattr(location_state, 'is_sealed'):
                    return location_state.is_sealed
                # Check for lockdown flag
                if hasattr(location_state, 'in_lockdown') and location_state.in_lockdown:
                    return True

        # Fall back to world config defaults
        if self.loader:
            try:
                world_config = self.loader.load_world_config()
                location_config = world_config.locations.get(location_id)
                if location_config and hasattr(location_config, 'default_sealed'):
                    # Note: default_sealed=True means normally sealed, not emergency sealed
                    # For gameplay, we only block if there's an active seal/lockdown
                    # Default sealed just means the area has a door that CAN be sealed
                    pass
            except Exception:
                pass

        # By default, locations are not actively sealed (doors are open)
        return False

    def _get_location_name(self, location_id: str) -> str:
        """Get display name for a location."""
        if self.loader:
            try:
                world_config = self.loader.load_world_config()
                location_config = world_config.locations.get(location_id)
                if location_config and hasattr(location_config, 'name'):
                    return location_config.name
            except Exception:
                pass

        # Fallback: convert ID to readable name
        return location_id.replace("_", " ").title()

    def get_priority(self) -> int:
        """High priority - check seals before atmosphere."""
        return 10
