"""Rules for parsing and validating AI outputs."""
from app.core.rules.base_rule import BaseRule, RuleResult


class NarrationValidationRule(BaseRule):
    """Rule for validating AI narration output."""

    async def validate(self, game_state, context: dict) -> RuleResult:
        """Validate narration content."""
        raise NotImplementedError

    async def apply(self, game_state, context: dict) -> RuleResult:
        """Apply validated narration."""
        raise NotImplementedError


class ActionExtractionRule(BaseRule):
    """Rule for extracting action effects from AI output."""

    async def validate(self, game_state, context: dict) -> RuleResult:
        """Validate extracted actions."""
        raise NotImplementedError

    async def apply(self, game_state, context: dict) -> RuleResult:
        """Apply extracted actions to state."""
        raise NotImplementedError


class StateUpdateRule(BaseRule):
    """Rule for applying state updates from AI suggestions."""

    async def validate(self, game_state, context: dict) -> RuleResult:
        """Validate AI-suggested state updates."""
        raise NotImplementedError

    async def apply(self, game_state, context: dict) -> RuleResult:
        """Apply state updates."""
        raise NotImplementedError
