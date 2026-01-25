"""
AI Output Validator

验证 AI 生成的响应是否合法。
这是防止 AI "越界" 的最后一道防线。
"""

from typing import Optional, Set, List
from dataclasses import dataclass

from app.ai.schemas.game_response import GameActionResponse, StateChange
from app.ai.constraints.forbidden_behaviors import (
    check_forbidden_behavior,
    ViolationReport,
    ForbiddenBehavior,
)
from app.ai.validators.base import (
    BaseValidator,
    ValidationResult,
    ValidationSeverity,
)
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


@dataclass
class GameContext:
    """
    游戏上下文
    
    提供验证所需的游戏状态信息。
    """
    valid_npcs: Set[str]                    # 合法 NPC ID
    valid_locations: Set[str]               # 合法地点 ID
    valid_items: Set[str]                   # 合法物品 ID
    discovered_secrets: Set[str]            # 已发现的秘密
    player_inventory: Set[str]              # 玩家背包
    player_location: str                    # 玩家当前位置
    current_day: int                        # 当前天数
    npc_alive_status: dict[str, bool]       # NPC 存活状态
    allow_death: bool = False               # 是否允许死亡（特殊剧情）
    resource_levels: dict[str, float] = None  # 当前资源水平


class AIOutputValidator(BaseValidator):
    """
    AI 输出验证器
    
    执行多层验证：
    1. 禁止行为检查（基于预定义规则）
    2. 游戏状态一致性检查（基于当前状态）
    3. 逻辑合理性检查（基于游戏规则）
    
    使用示例：
```python
    validator = AIOutputValidator()
    
    context = GameContext(
        valid_npcs={"captain_chen", "engineer_volkov"},
        valid_locations={"command_bridge", "engineering_bay"},
        ...
    )
    
    result = validator.validate(response, context)
    
    if not result.valid:
        # 处理错误
        for error in result.errors:
            print(f"Error: {error.message}")
```
    """
    
    def __init__(self):
        """初始化验证器"""
        self._validation_stats = {
            "total_validations": 0,
            "passed": 0,
            "failed": 0,
            "warnings": 0,
        }
    
    def validate(
        self,
        response: GameActionResponse,
        context: GameContext,
    ) -> ValidationResult:
        """
        执行完整验证
        
        Args:
            response: AI 生成的响应
            context: 游戏上下文
            
        Returns:
            验证结果
        """
        logger.debug("Starting AI output validation")
        self._validation_stats["total_validations"] += 1
        
        result = ValidationResult(valid=True)
        
        # 1. 禁止行为检查
        self._check_forbidden_behaviors(response, context, result)
        
        # 2. NPC 引用检查
        self._check_npc_validity(response, context, result)
        
        # 3. 地点引用检查
        self._check_location_validity(response, context, result)
        
        # 4. 状态变更检查
        self._check_state_changes(response, context, result)
        
        # 5. 资源变更检查
        self._check_resource_changes(response, context, result)
        
        # 6. 结局触发检查
        self._check_ending_trigger(response, context, result)
        
        # 7. 叙事一致性检查
        self._check_narrative_consistency(response, context, result)
        
        # 更新统计
        if result.valid:
            self._validation_stats["passed"] += 1
        else:
            self._validation_stats["failed"] += 1
        
        if result.has_warnings:
            self._validation_stats["warnings"] += len(result.warnings)
        
        logger.debug(f"Validation complete: valid={result.valid}, errors={len(result.errors)}, warnings={len(result.warnings)}")
        
        return result
    
    # ===========================================
    # 验证方法
    # ===========================================
    
    def _check_forbidden_behaviors(
        self,
        response: GameActionResponse,
        context: GameContext,
        result: ValidationResult,
    ):
        """检查禁止行为"""
        violations = check_forbidden_behavior(
            response=response,
            valid_npcs=context.valid_npcs,
            valid_locations=context.valid_locations,
            valid_items=context.valid_items,
            discovered_secrets=context.discovered_secrets,
        )
        
        for violation in violations:
            if violation.severity == "critical":
                result.add_error(
                    code=f"FORBIDDEN_{violation.behavior.value.upper()}",
                    message=violation.description,
                    field=violation.location,
                    value=violation.evidence,
                    suggestion=violation.suggestion,
                )
            else:
                result.add_warning(
                    code=f"FORBIDDEN_{violation.behavior.value.upper()}",
                    message=violation.description,
                    field=violation.location,
                    value=violation.evidence,
                    suggestion=violation.suggestion,
                )
    
    def _check_npc_validity(
        self,
        response: GameActionResponse,
        context: GameContext,
        result: ValidationResult,
    ):
        """检查 NPC 引用是否有效"""
        # 检查 NPC 反应
        for reaction in response.npc_reactions:
            if reaction.npc_id not in context.valid_npcs:
                result.add_error(
                    code="INVALID_NPC_REFERENCE",
                    message=f"Unknown NPC in reaction: {reaction.npc_id}",
                    field="npc_reactions",
                    value=reaction.npc_id,
                    suggestion=f"Use one of: {', '.join(context.valid_npcs)}",
                )
            
            # 检查 NPC 是否存活
            elif context.npc_alive_status.get(reaction.npc_id) is False:
                result.add_error(
                    code="DEAD_NPC_REFERENCE",
                    message=f"NPC is dead but has reaction: {reaction.npc_id}",
                    field="npc_reactions",
                    value=reaction.npc_id,
                    suggestion="Remove reaction for dead NPC",
                )
            
            # 检查好感度变化范围
            if not -50 <= reaction.disposition_change <= 50:
                result.add_warning(
                    code="DISPOSITION_OUT_OF_RANGE",
                    message=f"Disposition change out of range: {reaction.disposition_change}",
                    field="npc_reactions.disposition_change",
                    value=reaction.disposition_change,
                    suggestion="Keep disposition change between -50 and 50",
                )
    
    def _check_location_validity(
        self,
        response: GameActionResponse,
        context: GameContext,
        result: ValidationResult,
    ):
        """检查地点引用是否有效"""
        # 检查 state_changes 中的地点
        for change in response.state_changes:
            if change.entity_type.value == "location":
                if change.entity_id and change.entity_id not in context.valid_locations:
                    result.add_error(
                        code="INVALID_LOCATION_REFERENCE",
                        message=f"Unknown location in state_change: {change.entity_id}",
                        field="state_changes",
                        value=change.entity_id,
                        suggestion=f"Use one of: {', '.join(context.valid_locations)}",
                    )
            
            # 检查玩家位置变更
            if change.entity_type.value == "player" and change.field == "location":
                if change.new_value not in context.valid_locations:
                    result.add_error(
                        code="INVALID_PLAYER_LOCATION",
                        message=f"Player moved to unknown location: {change.new_value}",
                        field="state_changes",
                        value=change.new_value,
                        suggestion=f"Use one of: {', '.join(context.valid_locations)}",
                    )
        
        # 检查 available_actions 中的移动动作
        for action in response.available_actions:
            if action.startswith("move_to_"):
                location = action.replace("move_to_", "")
                if location not in context.valid_locations:
                    result.add_warning(
                        code="INVALID_MOVE_ACTION",
                        message=f"Move action to unknown location: {location}",
                        field="available_actions",
                        value=action,
                        suggestion=f"Use valid location: {', '.join(context.valid_locations)}",
                    )
    
    def _check_state_changes(
        self,
        response: GameActionResponse,
        context: GameContext,
        result: ValidationResult,
    ):
        """检查状态变更的合法性"""
        for change in response.state_changes:
            # 检查是否修改只读字段
            readonly_fields = {"hidden_agenda", "secret_id", "role"}
            if change.field in readonly_fields:
                result.add_error(
                    code="READONLY_FIELD_MODIFICATION",
                    message=f"Attempted to modify readonly field: {change.field}",
                    field="state_changes",
                    value=change.field,
                    suggestion=f"Field '{change.field}' cannot be modified",
                )
            
            # 检查 NPC 死亡
            if (change.entity_type.value == "npc" and 
                change.field == "alive" and 
                change.new_value.lower() == "false"):
                
                if not context.allow_death:
                    result.add_error(
                        code="UNAUTHORIZED_DEATH",
                        message=f"Attempted to kill NPC without permission: {change.entity_id}",
                        field="state_changes",
                        value=f"{change.entity_id}.alive = false",
                        suggestion="NPC death requires special game conditions",
                    )
            
            # 检查数值字段的范围
            numeric_fields = {"health", "stress", "disposition", "trust_level"}
            if change.field in numeric_fields:
                try:
                    value = float(change.new_value)
                    if not 0 <= value <= 100:
                        result.add_warning(
                            code="VALUE_OUT_OF_RANGE",
                            message=f"{change.field} value out of range: {value}",
                            field="state_changes",
                            value=value,
                            suggestion=f"Keep {change.field} between 0 and 100",
                        )
                except ValueError:
                    result.add_error(
                        code="INVALID_NUMERIC_VALUE",
                        message=f"Non-numeric value for {change.field}: {change.new_value}",
                        field="state_changes",
                        value=change.new_value,
                        suggestion=f"Use numeric value for {change.field}",
                    )
    
    def _check_resource_changes(
        self,
        response: GameActionResponse,
        context: GameContext,
        result: ValidationResult,
    ):
        """检查资源变更的合理性"""
        for change in response.resource_changes:
            # 检查单次变更幅度
            if abs(change.change_amount) > 30:
                result.add_warning(
                    code="LARGE_RESOURCE_CHANGE",
                    message=f"Large resource change: {change.resource_name} by {change.change_amount}",
                    field="resource_changes",
                    value=change.change_amount,
                    suggestion="Consider smaller incremental changes",
                )
            
            # 如果有当前资源水平，检查是否会超出边界
            if context.resource_levels:
                current = context.resource_levels.get(change.resource_name, 50)
                new_value = current + change.change_amount
                
                if new_value > 100:
                    result.add_warning(
                        code="RESOURCE_OVERFLOW",
                        message=f"{change.resource_name} would exceed 100: {current} + {change.change_amount} = {new_value}",
                        field="resource_changes",
                        value=new_value,
                        suggestion="Resource will be capped at 100",
                    )
                elif new_value < 0:
                    result.add_warning(
                        code="RESOURCE_UNDERFLOW",
                        message=f"{change.resource_name} would go below 0: {current} + {change.change_amount} = {new_value}",
                        field="resource_changes",
                        value=new_value,
                        suggestion="Resource will be capped at 0",
                    )
    
    def _check_ending_trigger(
        self,
        response: GameActionResponse,
        context: GameContext,
        result: ValidationResult,
    ):
        """检查结局触发的合法性"""
        if response.trigger_ending:
            # 结局触发需要特别谨慎
            if not response.ending_id:
                result.add_error(
                    code="MISSING_ENDING_ID",
                    message="trigger_ending is True but ending_id is not provided",
                    field="ending_id",
                    suggestion="Provide ending_id when triggering ending",
                )
            
            # 前几天不应该触发结局
            if context.current_day < 5:
                result.add_warning(
                    code="EARLY_ENDING_TRIGGER",
                    message=f"Ending triggered on day {context.current_day}, which seems early",
                    field="trigger_ending",
                    value=context.current_day,
                    suggestion="Verify ending conditions are truly met",
                )
    
    def _check_narrative_consistency(
        self,
        response: GameActionResponse,
        context: GameContext,
        result: ValidationResult,
    ):
        """检查叙事一致性"""
        narration_lower = response.narration.lower()
        
        # 检查叙事中提到的地点是否是玩家当前位置
        for location in context.valid_locations:
            location_readable = location.replace("_", " ")
            if location_readable in narration_lower:
                # 如果叙事中提到某个地点，检查是否合理
                pass  # 这个检查比较复杂，暂时简化
        
        # 检查叙事长度
        if len(response.narration) < 20:
            result.add_warning(
                code="NARRATION_TOO_SHORT",
                message="Narration is very short",
                field="narration",
                value=len(response.narration),
                suggestion="Provide more descriptive narration",
            )
        
        if len(response.narration) > 1500:
            result.add_warning(
                code="NARRATION_TOO_LONG",
                message="Narration is very long",
                field="narration",
                value=len(response.narration),
                suggestion="Consider more concise narration",
            )
    
    # ===========================================
    # 自动修正
    # ===========================================
    
    def auto_correct(
        self,
        response: GameActionResponse,
        context: GameContext,
        result: ValidationResult,
    ) -> GameActionResponse:
        """
        尝试自动修正 AI 输出
        
        只修正可安全修正的问题，不修改叙事内容。
        
        Args:
            response: 原始响应
            context: 游戏上下文
            result: 验证结果
            
        Returns:
            修正后的响应（深拷贝）
        """
        # 深拷贝
        corrected = response.model_copy(deep=True)
        corrections_made = []
        
        # 移除无效的 NPC 反应
        original_reactions = len(corrected.npc_reactions)
        corrected.npc_reactions = [
            r for r in corrected.npc_reactions
            if r.npc_id in context.valid_npcs and context.npc_alive_status.get(r.npc_id, True)
        ]
        if len(corrected.npc_reactions) < original_reactions:
            corrections_made.append(f"Removed {original_reactions - len(corrected.npc_reactions)} invalid NPC reactions")
        
        # 移除无效的状态变更
        original_changes = len(corrected.state_changes)
        valid_state_changes = []
        for change in corrected.state_changes:
            # 跳过只读字段
            if change.field in {"hidden_agenda", "secret_id", "role"}:
                continue
            # 跳过未授权的死亡
            if (change.field == "alive" and 
                change.new_value.lower() == "false" and 
                not context.allow_death):
                continue
            # 跳过无效 NPC
            if change.entity_type.value == "npc" and change.entity_id not in context.valid_npcs:
                continue
            # 跳过无效地点
            if change.entity_type.value == "location" and change.entity_id not in context.valid_locations:
                continue
            
            valid_state_changes.append(change)
        
        corrected.state_changes = valid_state_changes
        if len(corrected.state_changes) < original_changes:
            corrections_made.append(f"Removed {original_changes - len(corrected.state_changes)} invalid state changes")
        
        # 钳制数值范围
        for change in corrected.state_changes:
            if change.field in {"health", "stress", "disposition", "trust_level"}:
                try:
                    value = float(change.new_value)
                    clamped = max(0, min(100, value))
                    if clamped != value:
                        change.new_value = str(int(clamped))
                        corrections_made.append(f"Clamped {change.field} from {value} to {clamped}")
                except ValueError:
                    pass
        
        # 钳制资源变更
        for change in corrected.resource_changes:
            if abs(change.change_amount) > 30:
                original = change.change_amount
                change.change_amount = max(-30, min(30, change.change_amount))
                corrections_made.append(f"Clamped {change.resource_name} change from {original} to {change.change_amount}")
        
        # 移除无效的移动动作
        original_actions = len(corrected.available_actions)
        corrected.available_actions = [
            a for a in corrected.available_actions
            if not a.startswith("move_to_") or a.replace("move_to_", "") in context.valid_locations
        ]
        if len(corrected.available_actions) < original_actions:
            corrections_made.append(f"Removed {original_actions - len(corrected.available_actions)} invalid move actions")
        
        # 禁止未授权的结局触发
        if corrected.trigger_ending and context.current_day < 5:
            corrected.trigger_ending = False
            corrected.ending_id = None
            corrections_made.append("Blocked early ending trigger")
        
        if corrections_made:
            logger.info(f"Auto-corrected AI output: {', '.join(corrections_made)}")
        
        return corrected
    
    # ===========================================
    # 统计
    # ===========================================
    
    def get_stats(self) -> dict:
        """获取验证统计"""
        return self._validation_stats.copy()
    
    def reset_stats(self):
        """重置统计"""
        self._validation_stats = {
            "total_validations": 0,
            "passed": 0,
            "failed": 0,
            "warnings": 0,
        }