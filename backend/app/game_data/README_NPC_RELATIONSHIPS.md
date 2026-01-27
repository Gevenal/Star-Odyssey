# NPC 初始关系种子配置指南

## 概述

`state_variables.json` 中的 `npc_relationships` 部分定义了 NPC 之间的**初始关系种子**。这些配置会在游戏开始时用于初始化 NPC 之间的关系，为 AI 生成剧情提供基础。

## 配置格式

```json
{
  "npc_relationships": {
    "NPC Name 1": {
      "NPC Name 2": -20,  // trust_level (-100 到 100)
      "secret_knowledge": ["知道某个秘密"],
      "voice_style": "说话方式描述"
    }
  }
}
```

### 字段说明

- **NPC Name**: 必须是 `npc_templates.json` 中定义的 NPC 名称（精确匹配）
- **trust_level**: 信任等级，范围 -100 到 100
  - `-100 到 -75`: 敌对 (HOSTILE)
  - `-75 到 -25`: 不友好 (UNFRIENDLY)
  - `-25 到 25`: 中性 (NEUTRAL)
  - `25 到 75`: 友好 (FRIENDLY)
  - `75 到 100`: 忠诚 (LOYAL)
- **secret_knowledge**: 该 NPC 对目标 NPC 了解的秘密（字符串数组）
- **voice_style**: 该 NPC 对目标 NPC 说话的方式（可选字符串）

## 使用示例

### 示例 1: 简单的信任关系

```json
{
  "Captain Elena Chen": {
    "Dr. Aris Ashford": -20
  }
}
```

这表示 Chen 对 Ashford 的信任等级是 -20（不友好）。

### 示例 2: 带秘密知识的关系

```json
{
  "Captain Elena Chen": {
    "Dr. Aris Ashford": -20,
    "secret_knowledge": [
      "Suspects Ashford may have sent unauthorized distress beacon",
      "Knows Ashford has been hiding research data"
    ]
  }
}
```

### 示例 3: 完整的双向关系

```json
{
  "Captain Elena Chen": {
    "Dr. Aris Ashford": -20,
    "secret_knowledge": ["Suspects Ashford may have sent unauthorized distress beacon"],
    "voice_style": "Speaks with authority, uses formal language when discussing Ashford"
  },
  "Dr. Aris Ashford": {
    "Captain Elena Chen": -20,
    "secret_knowledge": ["Knows Chen is willing to sacrifice individuals for the majority"],
    "voice_style": "Defensive and technical when around Chen"
  }
}
```

注意：双向关系可以有不同的 `trust_level`、`secret_knowledge` 和 `voice_style`。

## 工作原理

1. **游戏初始化时**：
   - `GameDataLoader.get_npc_initial_relationships()` 读取配置
   - 传递给 `NPCGenerator.generate_full_crew(initial_relationships=...)`

2. **生成关系时**：
   - 如果配置中有预设关系 → 使用预设值
   - 如果配置中没有 → 随机生成（基于性格兼容性）

3. **运行时**：
   - 关系存储在 `NPCState.relationships` 中
   - 可以通过游戏事件动态改变
   - AI 在生成对话时会读取这些关系

## 在 AI Prompt 中使用

关系数据会被格式化成字符串，包含在 NPC 的 prompt 中：

```
Captain Elena Chen's relationships with the crew:
- Dr. Aris Ashford: UNFRIENDLY (trust: -20). Knows: Suspects Ashford may have sent unauthorized distress beacon. Speaks about/to them: Speaks with authority, uses formal language when discussing Ashford. History: Captain Elena Chen and Dr. Aris Ashford had a significant disagreement about mission priorities early on.
```

这样 Gemini 就能生成符合关系设定的对话。

## 最佳实践

1. **只配置重要的关系**：不需要为所有 NPC 对都配置关系，只配置对剧情有影响的关键关系。

2. **使用有意义的 secret_knowledge**：这些秘密会成为 AI 生成剧情的素材，要写得具体且有趣。

3. **voice_style 要具体**：不要写"说话正式"，而是写"Speaks with authority, uses formal language when discussing Ashford"。

4. **考虑双向关系**：A 对 B 的看法和 B 对 A 的看法可能不同，这能创造更丰富的剧情张力。

## 注意事项

- NPC 名称必须与 `npc_templates.json` 中的 `name` 字段**完全匹配**（包括大小写和标点）
- 如果配置了关系但找不到对应的 NPC，该配置会被忽略
- 未配置的关系会使用随机生成算法（基于性格兼容性）
- 关系在游戏运行过程中会动态变化，初始配置只是起点
