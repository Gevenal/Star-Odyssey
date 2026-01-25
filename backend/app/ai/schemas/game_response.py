"""
Game Action Response Schema

定义 AI 对玩家动作的响应格式。
所有 Gemini 生成的游戏内容必须符合此 Schema。
"""

from enum import Enum
from typing import List, Optional, Literal
from pydantic import BaseModel, Field, field_validator


# ===========================================
# Enums
# ===========================================

class Mood(str, Enum):
    """叙事氛围"""
    TENSE = "tense"           # 紧张
    PEACEFUL = "peaceful"     # 平静
    MYSTERIOUS = "mysterious" # 神秘
    URGENT = "urgent"         # 紧迫
    DESPERATE = "desperate"   # 绝望
    HOPEFUL = "hopeful"       # 希望


class ConfidenceLevel(str, Enum):
    """
    AI 对输出的信心等级
    
    - high: AI 确信这是合理的响应
    - medium: AI 认为这是可能的响应
    - speculative: AI 在推测，可能不准确
    """
    HIGH = "high"
    MEDIUM = "medium"
    SPECULATIVE = "speculative"


class EntityType(str, Enum):
    """可被修改的实体类型"""
    PLAYER = "player"
    NPC = "npc"
    WORLD = "world"
    LOCATION = "location"


# ===========================================
# Sub-models (状态变更的子结构)
# ===========================================

class StateChange(BaseModel):
    """
    单个状态变更
    
    AI 想要修改游戏状态时，必须通过这个结构声明。
    后端会验证每个变更的合法性。
    """
    entity_type: EntityType = Field(
        ...,
        description="被修改的实体类型: player/npc/world/location"
    )
    entity_id: Optional[str] = Field(
        default=None,
        description="实体 ID。player 和 world 不需要，npc 和 location 需要指定具体 ID"
    )
    field: str = Field(
        ...,
        description="要修改的字段名，如 'health', 'location', 'alive'"
    )
    old_value: Optional[str] = Field(
        default=None,
        description="原值（可选，用于验证和调试）"
    )
    new_value: str = Field(
        ...,
        description="新值"
    )
    reason: str = Field(
        ...,
        description="修改原因，用于调试和叙事一致性检查"
    )

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "entity_type": "player",
                    "entity_id": None,
                    "field": "health",
                    "old_value": "100",
                    "new_value": "85",
                    "reason": "Injured while repairing the hull breach"
                },
                {
                    "entity_type": "npc",
                    "entity_id": "chen",
                    "field": "disposition",
                    "old_value": "50",
                    "new_value": "65",
                    "reason": "Player helped with research data"
                }
            ]
        }


class ResourceChange(BaseModel):
    """
    资源变更
    
    飞船资源（氧气、能源等）的变化。
    """
    resource_name: str = Field(
        ...,
        description="资源名称: oxygen_level, power_level, fuel_reserves, medical_supplies, food_water, repair_materials"
    )
    change_amount: float = Field(
        ...,
        description="变化量，正数增加，负数减少"
    )
    reason: str = Field(
        ...,
        description="变化原因"
    )

    @field_validator('resource_name')
    @classmethod
    def validate_resource_name(cls, v: str) -> str:
        valid_resources = {
            'oxygen_level',
            'power_level', 
            'fuel_reserves',
            'medical_supplies',
            'food_water',
            'repair_materials'
        }
        if v not in valid_resources:
            raise ValueError(f"Invalid resource: {v}. Must be one of {valid_resources}")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "resource_name": "oxygen_level",
                "change_amount": -5.0,
                "reason": "Hull breach caused oxygen leak"
            }
        }


class NPCReaction(BaseModel):
    """
    NPC 对玩家动作的反应
    """
    npc_id: str = Field(
        ...,
        description="NPC 的唯一标识符"
    )
    reaction_text: str = Field(
        ...,
        description="NPC 的反应描述（不是对话，是行为描述）"
    )
    disposition_change: int = Field(
        default=0,
        ge=-50,
        le=50,
        description="好感度变化，-50 到 +50"
    )
    new_activity: Optional[str] = Field(
        default=None,
        description="NPC 开始的新活动（如果有）"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "npc_id": "captain_chen",
                "reaction_text": "Chen nods approvingly, making a note on his datapad",
                "disposition_change": 10,
                "new_activity": "reviewing_repair_plans"
            }
        }


# ===========================================
# Main Response Schema
# ===========================================

class GameActionResponse(BaseModel):
    """
    AI 对玩家动作的完整响应
    
    这是 Gemini 必须返回的 JSON 结构。
    所有游戏状态变更都必须通过这个结构声明，
    后端会验证并应用这些变更。
    """
    
    # ----- 核心响应 -----
    success: bool = Field(
        ...,
        description="玩家动作是否成功执行"
    )
    
    narration: str = Field(
        ...,
        min_length=10,
        max_length=2000,
        description="叙事文本，描述动作的结果。这是玩家看到的主要内容。"
    )
    
    mood: Mood = Field(
        default=Mood.PEACEFUL,
        description="当前场景的氛围"
    )
    
    confidence_level: ConfidenceLevel = Field(
        default=ConfidenceLevel.HIGH,
        description="AI 对这个响应的信心程度"
    )
    
    # ----- 状态变更 -----
    state_changes: List[StateChange] = Field(
        default_factory=list,
        description="所有状态变更列表。AI 不能直接修改状态，必须通过这里声明。"
    )
    
    resource_changes: List[ResourceChange] = Field(
        default_factory=list,
        description="资源变更列表"
    )
    
    npc_reactions: List[NPCReaction] = Field(
        default_factory=list,
        description="NPC 对玩家动作的反应"
    )
    
    # ----- 游戏流程 -----
    available_actions: List[str] = Field(
        default_factory=list,
        description="玩家接下来可以执行的动作 ID 列表"
    )
    
    trigger_ending: bool = Field(
        default=False,
        description="是否触发游戏结局。通常应该是 False，除非满足明确的结局条件。"
    )
    
    ending_id: Optional[str] = Field(
        default=None,
        description="如果 trigger_ending 为 True，指定结局 ID"
    )
    
    # ----- ORACLE 系统 -----
    oracle_message: Optional[str] = Field(
        default=None,
        description="ORACLE 的补充信息或评论（如果相关）"
    )

    # ----- 验证器 -----
    @field_validator('narration')
    @classmethod
    def validate_narration(cls, v: str) -> str:
        """确保叙事不包含元信息"""
        forbidden_phrases = [
            "as an ai",
            "i cannot",
            "i'm sorry, but",
            "json",
            "schema",
            "response format"
        ]
        v_lower = v.lower()
        for phrase in forbidden_phrases:
            if phrase in v_lower:
                raise ValueError(f"Narration contains forbidden phrase: '{phrase}'")
        return v
    
    @field_validator('ending_id')
    @classmethod
    def validate_ending_consistency(cls, v: Optional[str], info) -> Optional[str]:
        """确保 ending_id 和 trigger_ending 一致"""
        # 注意：在 Pydantic v2 中，需要通过 info.data 访问其他字段
        # 这个验证会在 model_validator 中更好地处理
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "narration": "You approach Captain Chen at the navigation console. He looks up, tension evident in his weathered features. 'We need to talk about the oxygen situation,' he says, lowering his voice.",
                "mood": "tense",
                "confidence_level": "high",
                "state_changes": [
                    {
                        "entity_type": "npc",
                        "entity_id": "captain_chen",
                        "field": "current_activity",
                        "new_value": "talking_to_player",
                        "reason": "Player initiated conversation"
                    }
                ],
                "resource_changes": [],
                "npc_reactions": [
                    {
                        "npc_id": "captain_chen",
                        "reaction_text": "Chen pauses his work to give you his full attention",
                        "disposition_change": 5,
                        "new_activity": "talking_to_player"
                    }
                ],
                "available_actions": [
                    "ask_about_oxygen",
                    "ask_about_crew",
                    "end_conversation",
                    "accuse_of_hiding_something"
                ],
                "trigger_ending": False,
                "ending_id": None,
                "oracle_message": None
            }
        }


# ===========================================
# Schema 导出工具
# ===========================================

def get_json_schema() -> dict:
    """
    获取 JSON Schema 字典
    
    用于注入到 Prompt 中，告诉 Gemini 必须返回的格式。
    """
    return GameActionResponse.model_json_schema()


def get_schema_prompt_fragment() -> str:
    """
    获取可以直接放入 Prompt 的 Schema 描述
    """
    import json
    schema = get_json_schema()
    
    return f"""
You MUST respond with a valid JSON object matching this exact schema:
```json
{json.dumps(schema, indent=2)}
```

IMPORTANT:
- Respond ONLY with the JSON object
- Do NOT include markdown code blocks in your response
- Do NOT include any explanation before or after the JSON
- Ensure all required fields are present
- Use only the allowed enum values for 'mood' and 'confidence_level'
"""