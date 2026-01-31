# API 实现状态梳理

## 一、核心游戏流程 API (`/api/v1/game/*`)

### ✅ **已完全实现**

| API | 路径 | 状态 | 说明 |
|-----|------|------|------|
| `POST /game/start` | `/api/v1/game/start` | ✅ **已实现** | 创建游戏会话，初始化状态，返回 session_id |
| `POST /game/action` | `/api/v1/game/action` | ✅ **已实现** | **核心流程**：调用 `GameLoop.process_action`，包含完整的规则校验 → AI 生成 → 状态更新 → 保存 |
| `GET /game/state/{session_id}` | `/api/v1/game/state/{id}` | ✅ **已实现** | 获取当前游戏状态，调用 `GameLoop.get_state` |
| `POST /game/end-turn/{session_id}` | `/api/v1/game/end-turn/{id}` | ✅ **已实现** | 手动结束回合，调用 `GameLoop.advance_turn`（资源衰减、回合推进、结局检查） |

### ⚠️ **部分实现（返回空/占位数据）**

| API | 路径 | 状态 | 问题 |
|-----|------|------|------|
| `GET /game/actions/{session_id}` | `/api/v1/game/actions/{id}` | ⚠️ **返回空数组** | 返回 `actions=[]`，没有真正从 `player_actions.json` 过滤可用动作 |
| `POST /game/action/stream` | `/api/v1/game/action/stream` | ⚠️ **未实现** | 返回错误消息，没有真正的流式响应 |

### 📝 **TODO 项**

1. **`/game/start`**：
   - `TODO Phase 1: Generate opening narration with AI` - 开场叙事是硬编码的
   - `TODO Phase 1: Get initial available actions` - 返回硬编码的 `["explore_bridge", "check_systems", "talk_to_oracle"]`

2. **`/game/actions/{session_id}`**：
   - `TODO Phase 1: Implement action filtering based on game state` - 需要根据游戏状态过滤 `player_actions.json` 中的动作
   - `TODO: Parse from player_actions.json based on state` - 需要检查 location、resources、items、npc_present、required_flags、cooldown、one_time

3. **`/game/action/stream`**：
   - `TODO Phase 1: Implement streaming` - 需要实现真正的 SSE 流式响应

---

## 二、GameLoop 流程与 API 的关系

### ✅ **已实现的完整流程**（`POST /game/action`）

```
用户提交 action
    ↓
[API] submit_action() 
    ↓
[GameLoop] process_action()
    ↓
[1] 加载状态 (SessionStateManager.get_state)
    ↓
[2] RulesEngine.validate_action() ✅ **已实现**
    ├─ ResourceAvailabilityRule ✅ **已实现**（location, resources, items, npc, flags）
    ├─ LocationTopologyRule ✅ **已实现**（connected_to 检查）
    └─ 如果失败 → 400 错误，停止
    ↓
[3] Gemini AI 生成响应 ✅ **已实现**
    ├─ build_narrator_prompt()
    ├─ gemini_client.generate_structured()
    └─ 失败时有 fallback
    ↓
[4] 应用 resource_changes ✅ **已实现**
    ↓
[5] 应用 state_changes ✅ **已实现**
    ↓
[6] increment_turn() ✅ **已实现**
    ↓
[7] _check_ending() ✅ **已实现**（氧气、生命、回合数）
    ↓
[8] 保存到 MongoDB ✅ **已实现**
    ↓
[9] 返回 GameActionResponse ✅ **已实现**
```

**结论**：`POST /game/action` 这个**核心流程是完全实现的**，包括规则校验、AI 生成、状态更新、持久化。

---

## 三、其他 API 模块

### ⚠️ **Save/Load API** (`/api/v1/save/*`)

| API | 状态 | 说明 |
|-----|------|------|
| `POST /save` | ❌ **TODO** | `TODO: Implement save functionality` |
| `GET /save` | ❌ **TODO** | `TODO: Implement save listing` |
| `POST /save/load` | ❌ **TODO** | `TODO: Implement load functionality` |
| `DELETE /save/{save_id}` | ❌ **TODO** | `TODO: Implement save deletion` |

### ⚠️ **Debug API** (`/api/v1/debug/*`)

| API | 状态 | 说明 |
|-----|------|------|
| `GET /debug/state/{session_id}` | ❌ **TODO** | `TODO: Implement state dump` |
| `POST /debug/set-variable` | ❌ **TODO** | `TODO: Implement state variable setting` |
| `POST /debug/trigger-event` | ❌ **TODO** | `TODO: Implement event triggering` |
| `GET /debug/risks/{session_id}` | ❌ **TODO** | `TODO: Implement risk analysis` |
| `POST /debug/test-prompt` | ❌ **TODO** | `TODO: Implement AI prompt testing` |

---

## 四、总结

### ✅ **已实现的核心功能**

1. **游戏会话管理**：创建会话、获取状态
2. **动作处理流程**：完整的 `GameLoop.process_action`（规则校验 → AI → 状态更新 → 保存）
3. **规则引擎**：ResourceAvailabilityRule、LocationTopologyRule 已实现
4. **回合推进**：`advance_turn` 实现资源衰减和回合计数

### ⚠️ **需要实现的功能**

1. **`GET /game/actions/{session_id}`** - 根据游戏状态过滤可用动作（这是你队友遇到的问题）
2. **`POST /game/action/stream`** - 流式响应
3. **`POST /game/start`** - AI 生成开场叙事（目前是硬编码）
4. **Save/Load API** - 全部 TODO
5. **Debug API** - 全部 TODO

---

## 五、你队友的问题

**问题**：`GET /game/actions/${sessionId}` 返回空数组

**原因**：
- 代码第 239 行：`actions=[]` - 直接返回空数组
- 第 236 行有 TODO：`# TODO Phase 1: Implement action filtering based on game state`
- **还没有实现**根据游戏状态从 `player_actions.json` 过滤可用动作的逻辑

**解决方案**：
需要实现类似 `ResourceAvailabilityRule` 的逻辑，遍历 `player_actions.json` 中的所有动作，检查每个动作的 `requirements`（location、min_resource_levels、items、npc_present、required_flags），只返回满足条件的动作。

---

## 六、流程图与 API 的关系

**之前给出的流程图主要描述的是 `GameLoop.process_action` 的内部流程**，这个流程是**完全实现的**，并且通过 `POST /game/action` API 暴露。

**但是**：
- `GET /game/actions/{session_id}` 这个 API **还没有实现**，所以返回空数组
- 其他辅助 API（save、debug）也大多是 TODO

**所以你的队友说得对**：很多 API 确实还没有真正实现，但**核心的游戏循环流程（`POST /game/action`）是完全实现的**。
