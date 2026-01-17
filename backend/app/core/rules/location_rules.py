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

        current_location = game_state.player.location
        target_location = action.target_location

        # TODO: Implement topology check
        # world_config = self.data.load_world_config()
        # current_loc_config = world_config.locations.get(current_location)

        # if not current_loc_config:
        #     return RuleResult(valid=False, error=f"Unknown current location: {current_location}")

        # if target_location not in current_loc_config.connected_to:
        #     available = ", ".join(current_loc_config.connected_to)
        #     return RuleResult(
        #         valid=False,
        #         error=f"Cannot reach {target_location} from {current_location}",
        #         suggestion=f"Available locations: {available}"
        #     )

        return RuleResult(valid=True)


class AtmosphereAccessRule(BaseRule):
    """Validates player can safely access location based on atmosphere."""

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

        # TODO: Implement atmosphere check
        # location_state = game_state.world.get_location_state(action.target_location)

        # if location_state.atmosphere == Atmosphere.VACUUM:
        #     has_suit = "space_suit" in game_state.player.inventory
        #     if not has_suit:
        #         return RuleResult(
        #             valid=False,
        #             error="Cannot enter vacuum without space suit",
        #             suggestion="Find a space suit first"
        #         )

        # if location_state.atmosphere == Atmosphere.TOXIC:
        #     has_mask = "gas_mask" in game_state.player.inventory
        #     if not has_mask:
        #         return RuleResult(
        #             valid=False,
        #             error="Toxic atmosphere detected - need gas mask"
        #         )

        # if location_state.atmosphere == Atmosphere.LOW_OXYGEN:
        #     # Allow but warn
        #     return RuleResult(
        #         valid=True,
        #         suggestion="Warning: Low oxygen in this area"
        #     )

        return RuleResult(valid=True)


class LocationSealRule(BaseRule):
    """Validates location is not sealed/locked."""

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

        # TODO: Implement seal check
        # location_state = game_state.world.get_location_state(action.target_location)

        # if not location_state.is_sealed:
        #     # Location is open
        #     return RuleResult(valid=True)

        # # Check if player has access card
        # required_card = f"access_card_{action.target_location}"
        # if required_card in game_state.player.inventory:
        #     return RuleResult(valid=True)

        # # Check if captain can override
        # if "captain_keycard" in game_state.player.inventory:
        #     return RuleResult(valid=True)

        # return RuleResult(
        #     valid=False,
        #     error=f"Location sealed - need {required_card}",
        #     suggestion="Find access card or get captain's override"
        # )

        return RuleResult(valid=True)

    def get_priority(self) -> int:
        """High priority - check seals before atmosphere."""
        return 10
