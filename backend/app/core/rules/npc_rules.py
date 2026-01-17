"""NPC interaction rules."""
from app.core.rules.base_rule import BaseRule, RuleResult


class NPCInteractionRule(BaseRule):
    """Rule for player-NPC interactions."""

    async def validate(self, game_state, context: dict) -> RuleResult:
        """Validate NPC interaction."""
        raise NotImplementedError

    async def apply(self, game_state, context: dict) -> RuleResult:
        """Apply interaction effects."""
        raise NotImplementedError


class NPCTrustRule(BaseRule):
    """Rule for NPC trust/relationship management."""

    async def validate(self, game_state, context: dict) -> RuleResult:
        """Validate trust changes."""
        raise NotImplementedError

    async def apply(self, game_state, context: dict) -> RuleResult:
        """Apply trust updates."""
        raise NotImplementedError


class NPCBehaviorRule(BaseRule):
    """Rule for autonomous NPC behavior."""

    async def validate(self, game_state, context: dict) -> RuleResult:
        """Validate NPC action."""
        raise NotImplementedError

    async def apply(self, game_state, context: dict) -> RuleResult:
        """Apply NPC action effects."""
        raise NotImplementedError
