"""
AI Output Schemas

定义所有 AI 输出必须遵循的数据结构。
这些 Schema 确保 AI 返回可预测、可验证的结构化数据。
"""

from .game_response import (
    GameActionResponse,
    StateChange,
    ResourceChange,
    NPCReaction,
    Mood,
    ConfidenceLevel,
)

__all__ = [
    "GameActionResponse",
    "StateChange", 
    "ResourceChange",
    "NPCReaction",
    "Mood",
    "ConfidenceLevel",
]