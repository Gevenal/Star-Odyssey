"""Rules engine for aggregating and executing rules."""
from typing import List

from app.core.rules.base_rule import BaseRule, RuleResult
from app.models.action import PlayerAction
from app.models.game_state import GameState


class RulesEngine:
    """Aggregates and executes game rules."""

    def __init__(self, game_data_loader=None):
        """
        Initialize rules engine.

        Args:
            game_data_loader: GameDataLoader or None. If provided, enables
                ResourceAvailabilityRule and LocationTopologyRule with real checks.
                If None, only a no-op ResourceAvailabilityRule is registered (always valid).
        """
        self.rules: List[BaseRule] = []
        from app.core.rules.resource_rules import ResourceAvailabilityRule
        from app.core.rules.location_rules import LocationTopologyRule

        if game_data_loader is not None:
            self.register_rule(ResourceAvailabilityRule(game_data_loader))
            self.register_rule(LocationTopologyRule(game_data_loader))
        else:
            self.register_rule(ResourceAvailabilityRule())

    def register_rule(self, rule: BaseRule):
        """
        Register a rule with the engine.

        Args:
            rule: Rule instance to register
        """
        self.rules.append(rule)

    def register_rules(self, rules: List[BaseRule]):
        """
        Register multiple rules.

        Args:
            rules: List of rule instances
        """
        self.rules.extend(rules)

    async def validate_action(self, game_state: GameState, action: PlayerAction) -> RuleResult:
        """
        Validate action against all applicable rules.

        Args:
            game_state: Current GameState
            action: PlayerAction to validate

        Returns:
            RuleResult: Aggregated validation result
        """
        for rule in self.rules:
            result = rule.validate(action, game_state) 
            if not result.valid:
                return result
        
        return RuleResult(valid=True)

    async def apply_rules(self, game_state, context: dict) -> List[RuleResult]:
        """
        Apply all applicable rules.

        Args:
            game_state: Current GameState
            context: Application context

        Returns:
            List[RuleResult]: Results from all applied rules
        """
        raise NotImplementedError

    def get_rules_by_type(self, rule_type: type) -> List[BaseRule]:
        """
        Get all rules of a specific type.

        Args:
            rule_type: Rule class type

        Returns:
            List[BaseRule]: Matching rules
        """
        raise NotImplementedError

    def clear_rules(self):
        """Clear all registered rules."""
        self.rules = []