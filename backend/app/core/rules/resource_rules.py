"""Resource management rules."""

from app.core.rules.base_rule import BaseRule, RuleResult
from app.models.game_state import GameState
from app.models.action import PlayerAction


class ResourceAvailabilityRule(BaseRule):
    """Validates that required resources are available for action."""

    def validate(self, action: PlayerAction, game_state: GameState) -> RuleResult:
        """
        Check if player has sufficient resources to perform action.

        Args:
            action: Player action to validate
            game_state: Current game state

        Returns:
            RuleResult: Valid if resources sufficient
        """
        # TODO: Implement resource checking
        # action_config = game_data_loader.get_action(action.action_id)
        # if not action_config:
        #     return RuleResult(valid=False, error=f"Unknown action: {action.action_id}")

        # for resource_name, min_value in action_config.requirements.min_resource_levels.items():
        #     current = get_resource_value(game_state, resource_name)
        #     if current < min_value:
        #         return RuleResult(
        #             valid=False,
        #             error=f"Insufficient {resource_name}: need {min_value}, have {current}"
        #         )

        return RuleResult(valid=True)


class ResourceDecayRule(BaseRule):
    """Applies resource decay each turn."""

    def validate(self, game_state: GameState) -> RuleResult:
        """
        Validate decay can be applied (always true).

        Args:
            game_state: Current game state

        Returns:
            RuleResult: Always valid
        """
        return RuleResult(valid=True)

    def apply_decay(self, game_state: GameState) -> GameState:
        """
        Apply resource decay to all resources.

        Args:
            game_state: Current game state

        Returns:
            GameState: State with decayed resources
        """
        # TODO: Implement decay
        # Apply decay_rate from state_variables.json to each resource
        # game_state.world.resources.oxygen_level.current -= decay_rate
        # Ensure current doesn't go below min
        return game_state


class CriticalResourceRule(BaseRule):
    """Checks for critically low resources and triggers warnings."""

    def validate(self, game_state: GameState) -> RuleResult:
        """
        Check if any resources are at critical levels.

        Args:
            game_state: Current game state

        Returns:
            RuleResult: Valid with metadata about critical resources
        """
        # TODO: Implement critical resource detection
        # critical_resources = []
        # if game_state.world.resources.oxygen_level.is_critical():
        #     critical_resources.append("oxygen")
        # ... check all resources

        # return RuleResult(
        #     valid=True,
        #     metadata={"critical_resources": critical_resources}
        # )

        return RuleResult(valid=True)
