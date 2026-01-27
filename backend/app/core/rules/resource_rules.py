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
