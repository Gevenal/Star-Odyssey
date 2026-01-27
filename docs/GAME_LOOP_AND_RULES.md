# GameLoop、RulesEngine 与 AI Validator 说明

## 一、GameLoop 做了什么

`GameLoop` 是**一局游戏的主循环**：收到玩家的一个“动作意图”，协调规则校验、AI 生成、状态更新和持久化。

### `process_action(session_id, action: PlayerAction)` 流程

```
1. 加载 state
   state_data = state_manager.get_state(session_id)
   GameStateManager.load_snapshot(state_data)

2. 若 game_meta.game_phase == "ending" → raise ValueError("Game has ended")

3. 校验「玩家动作」← RulesEngine（见下）
   game_state_pydantic = StateConverter.snapshot_to_game_state(...)
   validation_result = rules_engine.validate_action(game_state_pydantic, action)
   if not validation_result.valid:
       raise ValueError(validation_result.error)   # → API 返回 400

4. 调 Gemini 生成「叙事 + 结构化结果」
   ai_resp = gemini_client.generate_structured(..., response_model=AIGameActionResponse)
   （含：narration, resource_changes, state_changes, npc_reactions, available_actions, trigger_ending, ending_id 等）

5. 应用 AI 的 resource_changes、state_changes 到 GameStateManager
   （这里没有再用 RulesEngine，也没有用 ai/validators）

6. increment_turn；_check_ending（氧气、血量、回合上限）；必要时写 game_meta.game_phase = "ending"

7. state_manager.update_state(session_id, snapshot)

8. 把 ai_resp 转成 GameActionResponse 返回
```

所以：

- **RulesEngine 只校验「玩家的动作」**（`PlayerAction`），不校验 Gemini 的输出。
- **Gemini 的输出**（`resource_changes`、`state_changes` 等）在 GameLoop 里**直接被 apply**，没有经过 `app.ai.validators` 的 `AIOutputValidator`。

---

## 二、RulesEngine 做了什么

### 1. 校验对象：**玩家的动作（PlayerAction）**

- `action` = 用户在前端/API 提交的 **PlayerAction**：
  - `session_id`, `action_type`, `action_id`, `action_text`
  - `target_location`, `target_npc`, `target_item`（可选）

也就是**玩家“想做什么”**，不是 AI 的叙事或状态修改。

### 2. 作用：在调 Gemini 之前，判断这个动作在**当前游戏状态下是否允许**

- 例如（规则实现后可以做的事）：
  - 资源是否够（`ResourceAvailabilityRule`）
  - 目标地点是否连通、大气是否允许、是否被封锁（`LocationTopologyRule`、`AtmosphereAccessRule`、`LocationSealRule`）
  - 目标 NPC 是否存在、是否存活等

### 3. 当前实现

- `RulesEngine.validate_action(game_state, action)`：
  - 遍历已注册的 rules，对每个 rule 调用 `rule.validate(action, game_state)`；
  - 若某个 rule 返回 `RuleResult(valid=False, error=...)`，**立即返回该 RuleResult**（短路）；
  - 若全部通过，返回 `RuleResult(valid=True)`。
- 现在**只注册了 `ResourceAvailabilityRule`**，且其内部是 TODO，**始终返回 `valid=True`**，所以目前相当于“不拦截任何玩家动作”。

### 4. 若不合理会怎样

- `validate_action` 返回 `RuleResult(valid=False, error="...")`；
- GameLoop 中：
  ```python
  if not validation_result.valid:
      raise ValueError(validation_result.error or "Action invalid")
  ```
- API 捕获 `ValueError`，根据 message 返回 **400**，并带 `detail=error`。

也就是说：**只要有一条规则判为 invalid，就不会调 Gemini，也不会改 state，只给客户端 400**。

---

## 三、“action” 是用户选择还是 Gemini 的结果？

| 概念 | 含义 | 谁产生 | 谁校验 |
|------|------|--------|--------|
| **PlayerAction** | 玩家“想做什么”的请求：`action_id`、`action_text`、`target_*` 等 | 用户（前端/API） | **RulesEngine**（在调 Gemini 之前） |
| **AIGameActionResponse** | 叙事 + `resource_changes`、`state_changes`、`npc_reactions`、`available_actions`、`trigger_ending` 等 | **Gemini** | 目前：仅 Pydantic 的 `generate_structured` 做 schema 校验；**未**用 `ai/validators` |

所以：

- **RulesEngine 的“action” = 用户选择（PlayerAction）**，和 Gemini 无关。
- **Gemini 生成的是“后果”**：根据 PlayerAction + 当前 state 生成叙事和 state/resource/npc 变化；这些**没有**再经过 RulesEngine。

---

## 四、RulesEngine 和 `ai/validators` 的关系

### 1. 分工

| 组件 | 校验对象 | 时机 | 目的 |
|------|----------|------|------|
| **RulesEngine** | 用户的 **PlayerAction** | 在调用 Gemini **之前** | 判断“玩家能不能做这个动作”：资源、地点、NPC、封锁等 |
| **ai/validators（AIOutputValidator）** | Gemini 的 **GameActionResponse** | 在 Gemini 返回**之后**、应用 state 之前（若接入） | 判断“AI 给出的叙事和状态修改是否合法、安全”：禁止行为、无效 NPC/地点、只读字段、资源越界、过早结局等 |

### 2. 当前是否接在 GameLoop 里

- **RulesEngine**：已接入。`process_action` 第 3 步会调用 `rules_engine.validate_action`，不通过就 `raise ValueError`。
- **AIOutputValidator**：**未接入**。  
  - `process_action` 在拿到 `AIGameActionResponse` 后，直接 `gs.modify` / `gs.set(..., validate=False)`，没有调用 `AIOutputValidator.validate`，也没有用 `auto_correct`。

因此：

- 和 **Gemini 有关** 的是：**AI 的 GameActionResponse**；
- 和 **RulesEngine 有关** 的是：**用户的 PlayerAction**；
- **ai/validators** 设计上是用来**校验 Gemini 的 GameActionResponse** 的，和 RulesEngine 各管一段，但**目前只有 RulesEngine 被 GameLoop 使用**。

---

## 五、若要把 AIOutputValidator 接进 GameLoop（可选）

可以在「拿到 `ai_resp` 之后、apply 之前」加一步，例如：

```python
# 3.5. （可选）校验 / 修正 AI 输出
from app.ai.validators.output_validator import AIOutputValidator, GameContext

ctx = GameContext(
    valid_npcs=set(gs.state.get("npcs", {}).keys()),
    valid_locations=set(gs.state.get("locations", {}).keys()),
    valid_items=set(gs.state.get("player", {}).get("inventory", [])),
    ...
)
v = AIOutputValidator()
res = v.validate(ai_resp, ctx)
if not res.valid and res.has_errors:
    # 选一：直接拒绝，用 fallback 或重试
    ai_resp = fallback_ai_response(...)
else:
    ai_resp = v.auto_correct(ai_resp, ctx, res)  # 或只在不 valid 时 correct
# 然后再做 4. Apply resource_changes / state_changes
```

这样 RulesEngine 仍只负责 **PlayerAction**，AIOutputValidator 只负责 **AIGameActionResponse**，两阶段都生效。

---

## 六、改动状态与测试

### 1. 改动是否结束

- **GameLoop**：`process_action`、`advance_turn`、`get_state`、`initialize`、`process_action_stream` 的流程和依赖（RulesEngine、Gemini、StateConverter、GameStateManager）都已实现并可跑。
- **RulesEngine**：  
  - **引擎本身**：`validate_action` 的调用链、短路逻辑、以及“invalid → ValueError → 400”的对接都已完成。  
  - **具体规则**：  
    - `ResourceAvailabilityRule`：逻辑仍是 TODO，恒返回 `valid=True`；  
    - `LocationTopologyRule`、`AtmosphereAccessRule`、`LocationSealRule` 等：未在 `RulesEngine` 中注册，且多数为 TODO。  

所以：**流程和“判 invalid 就 400”的机制已经就绪；规则内容还需要你按设计补完**。

### 2. 测试是否覆盖

- **`test_phase0.sh`**：覆盖的是 HTTP 端到端（建局、`/action`、`/state`、`/end-turn`），会间接用到 GameLoop 和 RulesEngine，但**没有单测**：
  - 不会断言 `validate_action` 的入参、返回值；
  - 不会断言“某条规则故意返回 invalid 时是否 400”；
  - 不会 mock Gemini，单独测 GameLoop 逻辑。
- **`tests/test_game_loop.py`**、**`tests/test_rules_engine.py`**：原本大多是 `pass` 或 TODO，**没有真正调用 GameLoop / RulesEngine**。

**已补充的测试**（`tests/test_rules_engine.py`、`tests/test_game_loop.py`）：

- **RulesEngine**：`test_validate_action_success`（当前规则全通过）、`test_validate_action_fail_short_circuit`（一条规则返回 invalid）、`test_validate_action_fail_then_pass`（失败规则在前时短路）。
- **GameLoop**：`test_process_action_returns_response`（mock 下 `process_action` 返回正确且会持久化）、`test_process_action_invalid_raises`（`rules_engine` 返回 invalid 时 `ValueError`，且**不**调 Gemini、不 `update_state`）。

运行：

```bash
docker-compose run --rm -e GEMINI_API_KEY=dummy -e MONGODB_URI=mongodb://mongodb:27017 backend \
  python -m pytest tests/test_rules_engine.py::TestRulesEngine tests/test_game_loop.py -v
```

---

## 七、小结表

| 问题 | 答案 |
|------|------|
| RulesEngine 判断的是谁？ | **玩家的 PlayerAction**（用户选择：做什么、对谁、去哪）。 |
| 若判为不合理会怎样？ | `validate_action` 返回 `valid=False` → GameLoop `raise ValueError` → API 返回 **400**，**不调 Gemini，不改 state**。 |
| “action” 是用户的选择还是 Gemini 的？ | **用户的选择**。Gemini 只生成“后果”（叙事 + `resource_changes` / `state_changes` 等）。 |
| 和 `ai/validators` 的关系？ | **RulesEngine** 管 **PlayerAction**；**AIOutputValidator** 设计用来管 **Gemini 的 GameActionResponse**。前者已在 GameLoop 中；后者目前**未**接入。 |
| 改动做完了吗？ | 流程、引擎、invalid→400 都做了；**具体规则大多仍是 TODO**。 |
| 有覆盖这部分的测试吗？ | `test_phase0.sh` 间接覆盖；**专门针对 GameLoop / RulesEngine 的单测之前没有**，下文会补。 |
