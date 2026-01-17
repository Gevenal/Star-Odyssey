"""Base rule interface."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Any


@dataclass
class RuleResult:
    """Result of a rule validation."""

    valid: bool
    error: Optional[str] = None
    suggestion: Optional[str] = None
    metadata: Optional[dict[str, Any]] = None


class BaseRule(ABC):
    """Abstract base for all game rules."""

    def __init__(self):
        """Initialize rule."""
        self.rule_id: str = self.__class__.__name__
        self.description: str = self.__doc__ or "No description"

    @abstractmethod
    def validate(self, *args, **kwargs) -> RuleResult:
        """
        Validate and return result.

        Returns:
            RuleResult: Validation result with error/suggestion if invalid
        """
        pass

    def get_priority(self) -> int:
        """
        Get rule priority for execution order.

        Returns:
            int: Priority (higher = earlier execution). Default is 0.
        """
        return 0
