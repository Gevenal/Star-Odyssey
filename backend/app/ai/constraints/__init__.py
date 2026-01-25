"""
AI Constraints Module

定义 AI 行为的边界和限制。
这些约束确保 AI 在游戏规则内运行。
"""

from .forbidden_behaviors import (
    ForbiddenBehavior,
    FORBIDDEN_BEHAVIORS,
    FORBIDDEN_PATTERNS,
    check_forbidden_behavior,
    get_forbidden_behaviors_prompt,
)

__all__ = [
    "ForbiddenBehavior",
    "FORBIDDEN_BEHAVIORS",
    "FORBIDDEN_PATTERNS",
    "check_forbidden_behavior",
    "get_forbidden_behaviors_prompt",
]