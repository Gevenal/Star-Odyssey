#!/usr/bin/env python3
"""
测试 Gemini Client

运行: python scripts/test_gemini_client.py
cd backend

# 确保环境变量设置
export GEMINI_API_KEY=your-api-key-here

# 或者确保 .env 文件有这个 key

# 运行测试
python scripts/test_gemini_client.py
"""

import asyncio
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.ai.gemini_client import GeminiClient
from app.ai.schemas.game_response import GameActionResponse, get_schema_prompt_fragment


async def test_basic_generation():
    """测试基础文本生成"""
    print("\n" + "="*50)
    print("TEST 1: Basic Generation")
    print("="*50)
    
    client = GeminiClient()
    
    # 测试 Pro
    print("\n[Testing Gemini Pro]")
    response = await client.generate(
        "Say 'Odyssey-7 Pro connection successful!' in a dramatic space captain voice.",
        model="pro"
    )
    print(f"Pro Response: {response[:200]}...")
    
    # 测试 Flash
    print("\n[Testing Gemini Flash]")
    response = await client.generate(
        "Reply with just: 'Flash ready!'",
        model="flash"
    )
    print(f"Flash Response: {response}")
    
    print("\n✅ Basic generation test passed!")


async def test_structured_generation():
    """测试结构化输出生成"""
    print("\n" + "="*50)
    print("TEST 2: Structured Generation")
    print("="*50)
    
    client = GeminiClient()
    
    prompt = """
You are the narrator for a space survival game. The player just performed this action:
"Talk to Captain Chen about the oxygen situation"

Current context:
- Location: Command Bridge
- Captain Chen is present, looking stressed
- Oxygen is at 75% and slowly declining

Generate a response for this action.
"""
    
    print("\n[Generating structured response...]")
    
    response = await client.generate_structured(
        prompt=prompt,
        response_model=GameActionResponse,
        model="pro",
        temperature=0.7
    )
    
    print(f"\n✅ Response parsed successfully!")
    print(f"   Success: {response.success}")
    print(f"   Mood: {response.mood}")
    print(f"   Confidence: {response.confidence_level}")
    print(f"   Narration: {response.narration[:150]}...")
    print(f"   State changes: {len(response.state_changes)}")
    print(f"   NPC reactions: {len(response.npc_reactions)}")
    print(f"   Available actions: {response.available_actions}")


async def test_stream_generation():
    """测试流式生成"""
    print("\n" + "="*50)
    print("TEST 3: Stream Generation")
    print("="*50)
    
    client = GeminiClient()
    
    print("\n[Streaming response...]")
    print("-" * 40)
    
    char_count = 0
    async for chunk in client.generate_stream(
        "Describe a tense moment on a damaged spaceship in 2-3 sentences.",
        model="flash"
    ):
        print(chunk, end="", flush=True)
        char_count += len(chunk)
    
    print("\n" + "-" * 40)
    print(f"\n✅ Streamed {char_count} characters")


async def test_schema_output():
    """显示 Schema 信息"""
    print("\n" + "="*50)
    print("TEST 4: Schema Information")
    print("="*50)
    
    print("\n[JSON Schema fragment for prompts:]")
    print(get_schema_prompt_fragment()[:500] + "...")
    print("\n✅ Schema export working!")


async def main():
    """运行所有测试"""
    print("\n🚀 Gemini Client Test Suite")
    print("=" * 50)
    
    try:
        await test_basic_generation()
        await test_structured_generation()
        await test_stream_generation()
        await test_schema_output()
        
        print("\n" + "="*50)
        print("🎉 ALL TESTS PASSED!")
        print("="*50 + "\n")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())