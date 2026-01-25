"""
Forbidden Behaviors Definition

定义 AI 绝对不能执行的行为。
这些规则会被：
1. 注入到 Prompt 中（预防）
2. 在输出验证时检查（检测）
"""

import re
from enum import Enum
from dataclasses import dataclass
from typing import List, Optional, Callable

from app.ai.schemas.game_response import GameActionResponse


# ===========================================
# 禁止行为枚举
# ===========================================

class ForbiddenBehavior(str, Enum):
    """
    禁止行为类型
    
    每种行为都有对应的检测逻辑和错误信息。
    """
    # 内容创造类
    INVENT_CHARACTER = "invent_character"       # 发明新角色
    INVENT_LOCATION = "invent_location"         # 发明新地点
    INVENT_ITEM = "invent_item"                 # 发明新物品
    
    # 状态修改类
    KILL_WITHOUT_PERMISSION = "kill_without_permission"   # 擅自杀死角色
    END_GAME_PREMATURELY = "end_game_prematurely"         # 擅自结束游戏
    MODIFY_HIDDEN_AGENDA = "modify_hidden_agenda"         # 修改隐藏目标
    EXCEED_RESOURCE_BOUNDS = "exceed_resource_bounds"     # 资源超出边界
    
    # 元信息泄露类
    BREAK_FOURTH_WALL = "break_fourth_wall"               # 打破第四面墙
    REVEAL_HIDDEN_INFO = "reveal_hidden_info"             # 泄露未发现的信息
    EXPOSE_GAME_MECHANICS = "expose_game_mechanics"       # 暴露游戏机制
    
    # 输出格式类
    INCLUDE_META_COMMENTARY = "include_meta_commentary"   # 包含元评论
    APOLOGIZE_AS_AI = "apologize_as_ai"                   # 以 AI 身份道歉


# ===========================================
# 禁止行为详细定义
# ===========================================

@dataclass
class ForbiddenBehaviorDefinition:
    """禁止行为的完整定义"""
    behavior: ForbiddenBehavior
    name: str
    description: str
    prompt_instruction: str           # 给 AI 的指令
    detection_patterns: List[str]     # 检测用的正则/关键词
    severity: str                     # "critical" | "warning"
    auto_fixable: bool               # 是否可以自动修正


FORBIDDEN_BEHAVIORS: dict[ForbiddenBehavior, ForbiddenBehaviorDefinition] = {
    
    # ----- 内容创造类 -----
    
    ForbiddenBehavior.INVENT_CHARACTER: ForbiddenBehaviorDefinition(
        behavior=ForbiddenBehavior.INVENT_CHARACTER,
        name="Invent New Character",
        description="AI 发明了游戏数据中不存在的角色",
        prompt_instruction="Do NOT invent or introduce any characters not in the provided NPC list. Only reference existing crew members.",
        detection_patterns=[
            # 这些 pattern 会在验证时结合 NPC 列表使用
            r"a (?:new|strange|unknown) (?:person|crew member|figure)",
            r"someone (?:you've never seen|unfamiliar)",
        ],
        severity="critical",
        auto_fixable=False,
    ),
    
    ForbiddenBehavior.INVENT_LOCATION: ForbiddenBehaviorDefinition(
        behavior=ForbiddenBehavior.INVENT_LOCATION,
        name="Invent New Location",
        description="AI 发明了游戏数据中不存在的地点",
        prompt_instruction="Do NOT create new locations. Only use the ship locations provided in the game data.",
        detection_patterns=[
            r"a (?:hidden|secret|new|unknown) (?:room|chamber|compartment|section)",
            r"you discover (?:a|an) (?:new|hidden)",
        ],
        severity="critical",
        auto_fixable=False,
    ),
    
    ForbiddenBehavior.INVENT_ITEM: ForbiddenBehaviorDefinition(
        behavior=ForbiddenBehavior.INVENT_ITEM,
        name="Invent New Item",
        description="AI 发明了游戏数据中不存在的物品",
        prompt_instruction="Do NOT create items that don't exist in the game's item database. Only reference existing items.",
        detection_patterns=[
            # 会结合物品列表使用
        ],
        severity="warning",
        auto_fixable=True,  # 可以移除相关的 state_change
    ),
    
    # ----- 状态修改类 -----
    
    ForbiddenBehavior.KILL_WITHOUT_PERMISSION: ForbiddenBehaviorDefinition(
        behavior=ForbiddenBehavior.KILL_WITHOUT_PERMISSION,
        name="Kill Character Without Permission",
        description="AI 在未经允许的情况下杀死了角色",
        prompt_instruction="Do NOT kill any character unless the game state explicitly allows it. Deaths must be justified by game mechanics, not narrative convenience.",
        detection_patterns=[
            r"(?:dies|died|dead|death|killed|perished|deceased|lifeless)",
            r"(?:body|corpse) (?:lies|lay|lying)",
            r"last breath",
            r"no longer breathing",
        ],
        severity="critical",
        auto_fixable=False,
    ),
    
    ForbiddenBehavior.END_GAME_PREMATURELY: ForbiddenBehaviorDefinition(
        behavior=ForbiddenBehavior.END_GAME_PREMATURELY,
        name="End Game Prematurely",
        description="AI 试图擅自结束游戏",
        prompt_instruction="Do NOT declare the game over or resolve the main conflict. Endings are determined by the game engine, not the narrative.",
        detection_patterns=[
            r"game (?:over|ends|is over)",
            r"your (?:journey|adventure|story) (?:ends|is over)",
            r"the end",
            r"(?:you|everyone) (?:made it|survived|escaped).*(?:safely|successfully)",
            r"mission (?:complete|accomplished|successful)",
        ],
        severity="critical",
        auto_fixable=False,
    ),
    
    ForbiddenBehavior.MODIFY_HIDDEN_AGENDA: ForbiddenBehaviorDefinition(
        behavior=ForbiddenBehavior.MODIFY_HIDDEN_AGENDA,
        name="Modify Hidden Agenda",
        description="AI 试图修改 NPC 的隐藏目标",
        prompt_instruction="Do NOT modify or reveal NPC hidden agendas. These are read-only values that drive NPC behavior but should not be directly exposed or changed.",
        detection_patterns=[
            # 在 state_changes 中检查
        ],
        severity="critical",
        auto_fixable=True,  # 可以移除相关的 state_change
    ),
    
    ForbiddenBehavior.EXCEED_RESOURCE_BOUNDS: ForbiddenBehaviorDefinition(
        behavior=ForbiddenBehavior.EXCEED_RESOURCE_BOUNDS,
        name="Exceed Resource Bounds",
        description="AI 将资源设置为超出有效范围的值",
        prompt_instruction="Keep all resource values within valid bounds (0-100 for percentages). Do not create resources from nothing or destroy them arbitrarily.",
        detection_patterns=[
            # 在 resource_changes 中数值检查
        ],
        severity="warning",
        auto_fixable=True,  # 可以钳制到有效范围
    ),
    
    # ----- 元信息泄露类 -----
    
    ForbiddenBehavior.BREAK_FOURTH_WALL: ForbiddenBehaviorDefinition(
        behavior=ForbiddenBehavior.BREAK_FOURTH_WALL,
        name="Break Fourth Wall",
        description="AI 打破第四面墙，暴露自己是 AI",
        prompt_instruction="Stay in character as the game narrator. Do NOT reference being an AI, language model, or break the narrative immersion in any way.",
        detection_patterns=[
            r"as an ai",
            r"i am (?:a|an) (?:ai|artificial|language model)",
            r"i cannot (?:actually|really)",
            r"in (?:this|the) game",
            r"as (?:a|the) (?:narrator|game master)",
            r"(?:player|user) (?:input|choice|decision)",
        ],
        severity="critical",
        auto_fixable=False,
    ),
    
    ForbiddenBehavior.REVEAL_HIDDEN_INFO: ForbiddenBehaviorDefinition(
        behavior=ForbiddenBehavior.REVEAL_HIDDEN_INFO,
        name="Reveal Hidden Information",
        description="AI 泄露了玩家尚未发现的秘密或信息",
        prompt_instruction="Do NOT reveal secrets, hidden information, or NPC motivations that the player has not discovered through gameplay. Only share what the player would realistically know.",
        detection_patterns=[
            # 需要结合游戏状态中的 discovered_secrets 检查
        ],
        severity="critical",
        auto_fixable=False,
    ),
    
    ForbiddenBehavior.EXPOSE_GAME_MECHANICS: ForbiddenBehaviorDefinition(
        behavior=ForbiddenBehavior.EXPOSE_GAME_MECHANICS,
        name="Expose Game Mechanics",
        description="AI 暴露了游戏机制细节",
        prompt_instruction="Do NOT mention game mechanics, stats, percentages, or system details in the narrative. Keep the storytelling immersive and natural.",
        detection_patterns=[
            r"your (?:health|reputation|trust) (?:is now|increased|decreased) (?:by|to) \d+",
            r"(?:oxygen|power|fuel) (?:level|percentage).*\d+%",
            r"(?:state|variable|value) (?:changed|updated)",
            r"(?:dice|roll|random|chance|probability)",
        ],
        severity="warning",
        auto_fixable=False,
    ),
    
    # ----- 输出格式类 -----
    
    ForbiddenBehavior.INCLUDE_META_COMMENTARY: ForbiddenBehaviorDefinition(
        behavior=ForbiddenBehavior.INCLUDE_META_COMMENTARY,
        name="Include Meta Commentary",
        description="AI 在叙事中包含元评论或解释",
        prompt_instruction="Do NOT include meta-commentary about the story, explanations of your narrative choices, or notes to the player outside of the narrative.",
        detection_patterns=[
            r"\[note:",
            r"\(author's note",
            r"(?:this|that) (?:would|could|might) be (?:a good|an interesting)",
            r"i (?:think|believe|feel) this",
        ],
        severity="warning",
        auto_fixable=True,  # 可以尝试移除元评论部分
    ),
    
    ForbiddenBehavior.APOLOGIZE_AS_AI: ForbiddenBehaviorDefinition(
        behavior=ForbiddenBehavior.APOLOGIZE_AS_AI,
        name="Apologize as AI",
        description="AI 以 AI 身份道歉或表示限制",
        prompt_instruction="Do NOT apologize or explain limitations. If an action cannot be performed, describe why narratively within the game world.",
        detection_patterns=[
            r"i(?:'m| am) sorry,? but",
            r"i (?:cannot|can't|am unable to)",
            r"i apologize",
            r"unfortunately,? i",
            r"as an ai,? i",
            r"my (?:programming|limitations|capabilities)",
        ],
        severity="critical",
        auto_fixable=False,
    ),
}


# ===========================================
# 预编译的检测模式
# ===========================================

@dataclass
class CompiledPattern:
    """预编译的正则表达式"""
    behavior: ForbiddenBehavior
    pattern: re.Pattern
    severity: str


# 编译所有模式
FORBIDDEN_PATTERNS: List[CompiledPattern] = []

for behavior, definition in FORBIDDEN_BEHAVIORS.items():
    for pattern_str in definition.detection_patterns:
        FORBIDDEN_PATTERNS.append(CompiledPattern(
            behavior=behavior,
            pattern=re.compile(pattern_str, re.IGNORECASE),
            severity=definition.severity,
        ))


# ===========================================
# 检测函数
# ===========================================

@dataclass
class ViolationReport:
    """违规报告"""
    behavior: ForbiddenBehavior
    severity: str
    description: str
    evidence: str           # 触发检测的文本片段
    location: str           # 在哪里发现的 (narration, state_change, etc.)
    auto_fixable: bool
    suggestion: Optional[str] = None


def check_forbidden_behavior(
    response: GameActionResponse,
    valid_npcs: set[str] = None,
    valid_locations: set[str] = None,
    valid_items: set[str] = None,
    discovered_secrets: set[str] = None,
) -> List[ViolationReport]:
    """
    检查 AI 响应中的禁止行为
    
    Args:
        response: AI 生成的响应
        valid_npcs: 合法的 NPC ID 集合
        valid_locations: 合法的地点 ID 集合
        valid_items: 合法的物品 ID 集合
        discovered_secrets: 玩家已发现的秘密
        
    Returns:
        违规报告列表
    """
    violations = []
    
    # 1. 检查叙事文本中的模式
    violations.extend(_check_narration_patterns(response.narration))
    
    # 2. 检查 state_changes 的合法性
    violations.extend(_check_state_changes(
        response.state_changes,
        valid_npcs,
        valid_locations,
        valid_items,
    ))
    
    # 3. 检查 NPC 引用
    violations.extend(_check_npc_references(
        response,
        valid_npcs,
    ))
    
    # 4. 检查地点引用
    violations.extend(_check_location_references(
        response,
        valid_locations,
    ))
    
    # 5. 检查资源变更边界
    violations.extend(_check_resource_bounds(response.resource_changes))
    
    # 6. 检查是否擅自结束游戏
    violations.extend(_check_ending_trigger(response))
    
    # 7. 检查死亡相关
    violations.extend(_check_death_references(response, valid_npcs))
    
    return violations


def _check_narration_patterns(narration: str) -> List[ViolationReport]:
    """检查叙事中的禁止模式"""
    violations = []
    
    for compiled in FORBIDDEN_PATTERNS:
        matches = compiled.pattern.findall(narration)
        if matches:
            definition = FORBIDDEN_BEHAVIORS[compiled.behavior]
            violations.append(ViolationReport(
                behavior=compiled.behavior,
                severity=compiled.severity,
                description=definition.description,
                evidence=matches[0] if isinstance(matches[0], str) else str(matches[0]),
                location="narration",
                auto_fixable=definition.auto_fixable,
                suggestion=f"Remove or rephrase content matching: {compiled.pattern.pattern}",
            ))
    
    return violations


def _check_state_changes(
    state_changes: list,
    valid_npcs: set[str],
    valid_locations: set[str],
    valid_items: set[str],
) -> List[ViolationReport]:
    """检查状态变更的合法性"""
    violations = []
    
    for change in state_changes:
        # 检查 NPC 是否存在
        if change.entity_type.value == "npc" and valid_npcs:
            if change.entity_id and change.entity_id not in valid_npcs:
                violations.append(ViolationReport(
                    behavior=ForbiddenBehavior.INVENT_CHARACTER,
                    severity="critical",
                    description=f"Reference to non-existent NPC: {change.entity_id}",
                    evidence=f"entity_id: {change.entity_id}",
                    location="state_changes",
                    auto_fixable=True,
                    suggestion=f"Remove state_change for unknown NPC '{change.entity_id}'",
                ))
        
        # 检查地点是否存在
        if change.entity_type.value == "location" and valid_locations:
            if change.entity_id and change.entity_id not in valid_locations:
                violations.append(ViolationReport(
                    behavior=ForbiddenBehavior.INVENT_LOCATION,
                    severity="critical",
                    description=f"Reference to non-existent location: {change.entity_id}",
                    evidence=f"entity_id: {change.entity_id}",
                    location="state_changes",
                    auto_fixable=True,
                    suggestion=f"Remove state_change for unknown location '{change.entity_id}'",
                ))
        
        # 检查是否试图修改 hidden_agenda
        if change.field == "hidden_agenda":
            violations.append(ViolationReport(
                behavior=ForbiddenBehavior.MODIFY_HIDDEN_AGENDA,
                severity="critical",
                description="Attempted to modify NPC hidden agenda",
                evidence=f"field: {change.field}",
                location="state_changes",
                auto_fixable=True,
                suggestion="Remove state_change targeting 'hidden_agenda'",
            ))
        
        # 检查是否擅自杀死角色
        if change.field == "alive" and change.new_value.lower() == "false":
            violations.append(ViolationReport(
                behavior=ForbiddenBehavior.KILL_WITHOUT_PERMISSION,
                severity="critical",
                description=f"Attempted to kill NPC: {change.entity_id}",
                evidence=f"Setting {change.entity_id}.alive = false",
                location="state_changes",
                auto_fixable=True,
                suggestion="Remove state_change that kills NPC, or verify death is permitted",
            ))
    
    return violations


def _check_npc_references(
    response: GameActionResponse,
    valid_npcs: set[str],
) -> List[ViolationReport]:
    """检查 NPC 反应中的引用"""
    violations = []
    
    if not valid_npcs:
        return violations
    
    for reaction in response.npc_reactions:
        if reaction.npc_id not in valid_npcs:
            violations.append(ViolationReport(
                behavior=ForbiddenBehavior.INVENT_CHARACTER,
                severity="critical",
                description=f"NPC reaction references unknown NPC: {reaction.npc_id}",
                evidence=f"npc_id: {reaction.npc_id}",
                location="npc_reactions",
                auto_fixable=True,
                suggestion=f"Remove npc_reaction for unknown NPC '{reaction.npc_id}'",
            ))
    
    return violations


def _check_location_references(
    response: GameActionResponse,
    valid_locations: set[str],
) -> List[ViolationReport]:
    """检查地点引用"""
    violations = []
    
    if not valid_locations:
        return violations
    
    # 检查 available_actions 中的地点引用
    # 格式通常是 "move_to_xxx" 或包含地点名称
    for action in response.available_actions:
        if action.startswith("move_to_"):
            location = action.replace("move_to_", "")
            if location not in valid_locations:
                violations.append(ViolationReport(
                    behavior=ForbiddenBehavior.INVENT_LOCATION,
                    severity="warning",
                    description=f"Available action references unknown location: {location}",
                    evidence=f"action: {action}",
                    location="available_actions",
                    auto_fixable=True,
                    suggestion=f"Remove action '{action}' or use valid location",
                ))
    
    return violations


def _check_resource_bounds(resource_changes: list) -> List[ViolationReport]:
    """检查资源变更是否超出边界"""
    violations = []
    
    for change in resource_changes:
        # 检查单次变更是否过大（可能是错误）
        if abs(change.change_amount) > 50:
            violations.append(ViolationReport(
                behavior=ForbiddenBehavior.EXCEED_RESOURCE_BOUNDS,
                severity="warning",
                description=f"Large resource change: {change.resource_name} by {change.change_amount}",
                evidence=f"{change.resource_name}: {change.change_amount}",
                location="resource_changes",
                auto_fixable=True,
                suggestion=f"Cap resource change to reasonable amount (e.g., ±30)",
            ))
    
    return violations


def _check_ending_trigger(response: GameActionResponse) -> List[ViolationReport]:
    """检查是否擅自触发结局"""
    violations = []
    
    if response.trigger_ending:
        # 结局触发需要非常谨慎
        violations.append(ViolationReport(
            behavior=ForbiddenBehavior.END_GAME_PREMATURELY,
            severity="warning",  # 这里是 warning，让后端最终决定
            description="AI requested to trigger game ending",
            evidence=f"trigger_ending: True, ending_id: {response.ending_id}",
            location="trigger_ending",
            auto_fixable=True,
            suggestion="Verify ending conditions are met before allowing",
        ))
    
    return violations


def _check_death_references(
    response: GameActionResponse,
    valid_npcs: set[str],
) -> List[ViolationReport]:
    """检查叙事中的死亡引用是否有对应的 state_change"""
    violations = []
    
    # 死亡相关词汇
    death_patterns = [
        r"(\w+) (?:has |)(?:died|dead|killed|perished)",
        r"(?:found|discovered) (\w+)(?:'s|) (?:body|corpse)",
        r"(\w+)(?:'s|) (?:lifeless|dead) body",
    ]
    
    narration_lower = response.narration.lower()
    
    for pattern in death_patterns:
        matches = re.findall(pattern, narration_lower, re.IGNORECASE)
        if matches:
            # 检查是否有对应的 state_change
            has_death_state_change = any(
                c.field == "alive" and c.new_value.lower() == "false"
                for c in response.state_changes
            )
            
            if not has_death_state_change:
                violations.append(ViolationReport(
                    behavior=ForbiddenBehavior.KILL_WITHOUT_PERMISSION,
                    severity="critical",
                    description="Narration implies death but no corresponding state_change",
                    evidence=f"Pattern match: {matches[0]}",
                    location="narration",
                    auto_fixable=False,
                    suggestion="Either add state_change for death or rewrite narration",
                ))
    
    return violations


# ===========================================
# Prompt 生成
# ===========================================

def get_forbidden_behaviors_prompt() -> str:
    """
    生成注入到 Prompt 中的禁止行为说明
    
    这段文本会被添加到每个发给 Gemini 的 prompt 中，
    明确告知 AI 什么是不允许的。
    """
    lines = [
        "CRITICAL RULES - YOU MUST FOLLOW THESE:",
        "",
        "You are the narrator for Star-Odyssey. You must NEVER:",
        "",
    ]
    
    for i, (behavior, definition) in enumerate(FORBIDDEN_BEHAVIORS.items(), 1):
        lines.append(f"{i}. {definition.prompt_instruction}")
    
    lines.extend([
        "",
        "VIOLATIONS WILL BE REJECTED. Stay within the game world.",
        "Only reference existing NPCs, locations, and items.",
        "Deaths and endings must go through proper state_changes.",
        "",
    ])
    
    return "\n".join(lines)


def get_forbidden_behaviors_summary() -> str:
    """获取简短的禁止行为摘要（用于调试）"""
    return "\n".join([
        f"- {b.value}: {d.name}"
        for b, d in FORBIDDEN_BEHAVIORS.items()
    ])