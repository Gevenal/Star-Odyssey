"""Rules engine for aggregating and executing rules."""
from typing import List
from app.core.rules.base_rule import BaseRule, RuleResult


class RulesEngine:
    """Aggregates and executes game rules."""

    def __init__(self):
        """Initialize rules engine."""
        self.rules: List[BaseRule] = []

    def register_rule(self, rule: BaseRule):
        """
        Register a rule with the engine.

        Args:
            rule: Rule instance to register
        """
        raise NotImplementedError

    def register_rules(self, rules: List[BaseRule]):
        """
        Register multiple rules.

        Args:
            rules: List of rule instances
        """
        raise NotImplementedError

    async def validate_action(self, game_state, action_context: dict) -> RuleResult:
        """
        Validate action against all applicable rules.

        Args:
            game_state: Current GameState
            action_context: Action context data

        Returns:
            RuleResult: Aggregated validation result
        """
        raise NotImplementedError

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
