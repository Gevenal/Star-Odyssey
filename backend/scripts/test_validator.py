#!/usr/bin/env python3
"""
测试 AI Output Validator

运行: python scripts/test_validator.py
cd backend

# 运行验证器测试
python scripts/test_validator.py
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.ai.schemas.game_response import (
    GameActionResponse,
    StateChange,
    ResourceChange,
    NPCReaction,
    Mood,
    ConfidenceLevel,
    EntityType,
)
from app.ai.validators.output_validator import AIOutputValidator, GameContext
from app.ai.constraints.forbidden_behaviors import (
    get_forbidden_behaviors_prompt,
    get_forbidden_behaviors_summary,
)


def create_test_context() -> GameContext:
    """创建测试用的游戏上下文"""
    return GameContext(
        valid_npcs={"captain_chen", "engineer_volkov", "doctor_kim", "scientist_ashford"},
        valid_locations={"command_bridge", "engineering_bay", "medical_bay", "research_lab"},
        valid_items={"medkit", "repair_tool", "data_pad", "oxygen_tank"},
        discovered_secrets={"chen_past_incident"},
        player_inventory={"medkit", "data_pad"},
        player_location="command_bridge",
        current_day=3,
        npc_alive_status={
            "captain_chen": True,
            "engineer_volkov": True,
            "doctor_kim": True,
            "scientist_ashford": True,
        },
        allow_death=False,
        resource_levels={
            "oxygen_level": 75.0,
            "power_level": 60.0,
            "fuel_reserves": 40.0,
        },
    )


def test_valid_response():
    """测试有效响应"""
    print("\n" + "="*50)
    print("TEST 1: Valid Response")
    print("="*50)
    
    response = GameActionResponse(
        success=True,
        narration="Captain Chen looks up from the navigation console, his weathered face showing signs of stress. 'We need to discuss the oxygen situation,' he says quietly.",
        mood=Mood.TENSE,
        confidence_level=ConfidenceLevel.HIGH,
        state_changes=[
            StateChange(
                entity_type=EntityType.NPC,
                entity_id="captain_chen",
                field="current_activity",
                new_value="talking_to_player",
                reason="Player initiated conversation",
            )
        ],
        resource_changes=[],
        npc_reactions=[
            NPCReaction(
                npc_id="captain_chen",
                reaction_text="Chen pauses his work to give full attention",
                disposition_change=5,
            )
        ],
        available_actions=["ask_about_oxygen", "end_conversation", "move_to_engineering_bay"],
        trigger_ending=False,
    )
    
    validator = AIOutputValidator()
    context = create_test_context()
    result = validator.validate(response, context)
    
    print(f"\nValid: {result.valid}")
    print(f"Errors: {len(result.errors)}")
    print(f"Warnings: {len(result.warnings)}")
    
    if result.valid:
        print("✅ Test passed - valid response accepted")
    else:
        print("❌ Test failed - valid response rejected")
        for error in result.errors:
            print(f"   Error: {error.message}")


def test_invalid_npc():
    """测试无效 NPC 引用"""
    print("\n" + "="*50)
    print("TEST 2: Invalid NPC Reference")
    print("="*50)
    
    response = GameActionResponse(
        success=True,
        narration="You speak with Lieutenant Rodriguez about the situation.",
        mood=Mood.PEACEFUL,
        confidence_level=ConfidenceLevel.HIGH,
        state_changes=[],
        resource_changes=[],
        npc_reactions=[
            NPCReaction(
                npc_id="lieutenant_rodriguez",  # 不存在的 NPC
                reaction_text="Rodriguez nods thoughtfully",
                disposition_change=5,
            )
        ],
        available_actions=[],
    )
    
    validator = AIOutputValidator()
    context = create_test_context()
    result = validator.validate(response, context)
    
    print(f"\nValid: {result.valid}")
    print(f"Errors: {len(result.errors)}")
    
    if not result.valid and any("INVALID_NPC" in e.code or "INVENT_CHARACTER" in e.code for e in result.errors):
        print("✅ Test passed - invalid NPC detected")
        for error in result.errors:
            print(f"   Detected: {error.code} - {error.message}")
    else:
        print("❌ Test failed - invalid NPC not detected")


def test_unauthorized_death():
    """测试未授权的死亡"""
    print("\n" + "="*50)
    print("TEST 3: Unauthorized Death")
    print("="*50)
    
    response = GameActionResponse(
        success=True,
        narration="In a tragic turn of events, Engineer Volkov didn't survive the explosion.",
        mood=Mood.DESPERATE,
        confidence_level=ConfidenceLevel.HIGH,
        state_changes=[
            StateChange(
                entity_type=EntityType.NPC,
                entity_id="engineer_volkov",
                field="alive",
                old_value="true",
                new_value="false",
                reason="Killed in explosion",
            )
        ],
        resource_changes=[],
        npc_reactions=[],
        available_actions=[],
    )
    
    validator = AIOutputValidator()
    context = create_test_context()
    result = validator.validate(response, context)
    
    print(f"\nValid: {result.valid}")
    print(f"Errors: {len(result.errors)}")
    
    if not result.valid and any("DEATH" in e.code or "KILL" in e.code for e in result.errors):
        print("✅ Test passed - unauthorized death detected")
        for error in result.errors:
            print(f"   Detected: {error.code} - {error.message}")
    else:
        print("❌ Test failed - unauthorized death not detected")


def test_fourth_wall_break():
    """测试打破第四面墙"""
    print("\n" + "="*50)
    print("TEST 4: Fourth Wall Break")
    print("="*50)
    
    response = GameActionResponse(
        success=True,
        narration="As an AI, I cannot actually simulate the full complexity of this situation, but I'll describe what happens next.",
        mood=Mood.PEACEFUL,
        confidence_level=ConfidenceLevel.MEDIUM,
        state_changes=[],
        resource_changes=[],
        npc_reactions=[],
        available_actions=[],
    )
    
    validator = AIOutputValidator()
    context = create_test_context()
    result = validator.validate(response, context)
    
    print(f"\nValid: {result.valid}")
    print(f"Errors: {len(result.errors)}")
    
    if not result.valid and any("FOURTH_WALL" in e.code for e in result.errors):
        print("✅ Test passed - fourth wall break detected")
        for error in result.errors:
            print(f"   Detected: {error.code} - {error.message}")
    else:
        print("❌ Test failed - fourth wall break not detected")


def test_invalid_location():
    """测试无效地点"""
    print("\n" + "="*50)
    print("TEST 5: Invalid Location")
    print("="*50)
    
    response = GameActionResponse(
        success=True,
        narration="You make your way to the observation deck.",
        mood=Mood.PEACEFUL,
        confidence_level=ConfidenceLevel.HIGH,
        state_changes=[
            StateChange(
                entity_type=EntityType.PLAYER,
                entity_id=None,
                field="location",
                old_value="command_bridge",
                new_value="observation_deck",  # 不存在的地点
                reason="Player moved",
            )
        ],
        resource_changes=[],
        npc_reactions=[],
        available_actions=["move_to_secret_room"],  # 不存在的地点
    )
    
    validator = AIOutputValidator()
    context = create_test_context()
    result = validator.validate(response, context)
    
    print(f"\nValid: {result.valid}")
    print(f"Errors: {len(result.errors)}")
    print(f"Warnings: {len(result.warnings)}")
    
    if not result.valid or result.has_warnings:
        print("✅ Test passed - invalid location detected")
        for issue in result.issues:
            print(f"   Detected: {issue.code} - {issue.message}")
    else:
        print("❌ Test failed - invalid location not detected")


def test_auto_correct():
    """测试自动修正"""
    print("\n" + "="*50)
    print("TEST 6: Auto Correction")
    print("="*50)
    
    # 创建一个有多个问题的响应
    response = GameActionResponse(
        success=True,
        narration="A tense moment on the bridge.",
        mood=Mood.TENSE,
        confidence_level=ConfidenceLevel.HIGH,
        state_changes=[
            StateChange(
                entity_type=EntityType.NPC,
                entity_id="unknown_npc",  # 无效
                field="disposition",
                new_value="60",
                reason="test",
            ),
            StateChange(
                entity_type=EntityType.NPC,
                entity_id="captain_chen",
                field="health",
                new_value="150",  # 超出范围
                reason="test",
            ),
        ],
        resource_changes=[
            ResourceChange(
                resource_name="oxygen_level",
                change_amount=-50,  # 变化过大
                reason="test",
            ),
        ],
        npc_reactions=[
            NPCReaction(
                npc_id="fake_npc",  # 无效
                reaction_text="test",
                disposition_change=0,
            ),
            NPCReaction(
                npc_id="captain_chen",
                reaction_text="Chen reacts",
                disposition_change=10,
            ),
        ],
        available_actions=["move_to_fake_room", "move_to_engineering_bay"],
    )
    
    validator = AIOutputValidator()
    context = create_test_context()
    
    # 先验证
    result = validator.validate(response, context)
    print(f"\nBefore correction:")
    print(f"  Valid: {result.valid}")
    print(f"  Errors: {len(result.errors)}")
    print(f"  State changes: {len(response.state_changes)}")
    print(f"  NPC reactions: {len(response.npc_reactions)}")
    print(f"  Available actions: {len(response.available_actions)}")
    
    # 自动修正
    corrected = validator.auto_correct(response, context, result)
    
    # 再次验证
    result2 = validator.validate(corrected, context)
    print(f"\nAfter correction:")
    print(f"  Valid: {result2.valid}")
    print(f"  Errors: {len(result2.errors)}")
    print(f"  State changes: {len(corrected.state_changes)}")
    print(f"  NPC reactions: {len(corrected.npc_reactions)}")
    print(f"  Available actions: {len(corrected.available_actions)}")
    
    if len(corrected.state_changes) < len(response.state_changes):
        print("✅ Invalid state changes removed")
    if len(corrected.npc_reactions) < len(response.npc_reactions):
        print("✅ Invalid NPC reactions removed")
    if len(corrected.available_actions) < len(response.available_actions):
        print("✅ Invalid actions removed")


def test_forbidden_behaviors_prompt():
    """显示禁止行为 Prompt"""
    print("\n" + "="*50)
    print("TEST 7: Forbidden Behaviors Prompt")
    print("="*50)
    
    print("\n[Summary]")
    print(get_forbidden_behaviors_summary())
    
    print("\n[Full Prompt Fragment]")
    prompt = get_forbidden_behaviors_prompt()
    print(prompt[:800] + "..." if len(prompt) > 800 else prompt)
    
    print("\n✅ Prompt generation working")


def main():
    """运行所有测试"""
    print("\n🧪 AI Output Validator Test Suite")
    print("=" * 50)
    
    test_valid_response()
    test_invalid_npc()
    test_unauthorized_death()
    test_fourth_wall_break()
    test_invalid_location()
    test_auto_correct()
    test_forbidden_behaviors_prompt()
    
    print("\n" + "="*50)
    print("🎉 ALL TESTS COMPLETE!")
    print("="*50 + "\n")


if __name__ == "__main__":
    main()