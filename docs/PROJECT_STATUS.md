# Star-Odyssey 项目现状：功能、工作流、测试与已知问题

## 一、已实现功能与 Workflow

### 1. 游戏核心 (Game) — `/api/v1/game/*`

| 接口 | 方法 | 路径 | 状态 | 简要 Workflow |
|------|------|------|------|----------------|
| **Start Game** | POST | `/game/start` | ✅ 已实现 | `GameStartRequest(player_name)` → `SessionStateManager.create_session` → `GameStateManager` 初始化 → 入库 `sessions` → `StateConverter.snapshot_to_game_state` → 返回 `session_id`, `opening_narration`, `initial_state`, `available_actions`, `oracle_message`（开局叙事目前为固定文案，未用 AI） |
| **Submit Action** | POST | `/game/action` | ✅ 已实现 | `PlayerAction` → `GameLoop.process_action`: 加载 state → 规则校验 → **Gemini `generate_structured`(AIGameActionResponse)** → 应用 `resource_changes` / `state_changes` → `increment_turn` → `_check_ending` → 持久化 → 返回 `GameActionResponse` |
| **Get State** | GET | `/game/state/{session_id}` | ✅ 已实现 | `GameLoop.get_state` → `SessionStateManager.get_state` → `StateConverter.snapshot_to_game_state` → 返回 `GameState` |
| **End Turn** | POST | `/game/end-turn/{session_id}` | ✅ 已实现 | `GameLoop.advance_turn`: 加载 state → 若已 ending 则 `ValueError` → 对 `oxygen_level` / `fuel_reserves` / `power_level` / `food_water` 做固定 decay → `increment_turn` → `_check_ending` → 持久化 → 返回 `TurnEndResponse` 兼容 dict |
| **Submit Action (Stream)** | POST | `/game/action/stream` | ⚠️ 占位 | 固定返回 SSE：`{"type":"error","message":"Streaming not yet implemented. Use /action endpoint."}` |
| **Get Available Actions** | GET | `/game/actions/{session_id}` | ⚠️ 半实现 | 仅校验 session 存在；`actions=[]`，`context_hints` / `urgent_actions` 为写死占位，未按 state 过滤 |

### 2. 存档 (Save) — `/api/v1/save/*`

| 接口 | 方法 | 路径 | 状态 |
|------|------|------|------|
| Save | POST | `/save/save` | ❌ 501 未实现 |
| List Saves | GET | `/save/saves` | ❌ 501 未实现 |
| Load | POST | `/save/load/{save_id}` | ❌ 404 占位 |
| Delete Save | DELETE | `/save/save/{save_id}` | ❌ 404 占位 |

> 注：`SessionStateManager` 已有 `save_checkpoint` / `restore_checkpoint`，但 save 路由未对接。

### 3. 调试 (Debug) — `/api/v1/debug/*`（仅 `APP_ENV=development`）

| 接口 | 状态 |
|------|------|
| `GET /debug/state/dump/{session_id}` | ❌ 501 |
| `POST /debug/state/set-variable` | ❌ 501 |
| `POST /debug/trigger-event` | ❌ 501 |
| `GET /debug/explain-risks/{session_id}` | ❌ 501 |
| `POST /debug/ai/test-prompt` | ❌ 501 |

---

### 4. 核心 Workflow 示意

```
[Frontend]                    [Backend]
    |                             |
    |  POST /game/start           |
    |  {player_name}              |
    |---------------------------->|  SessionStateManager.create_session
    |                             |  GameStateManager(config_dir).set(player.name)
    |                             |  sessions.insert_one({_id, state: snapshot, ...})
    |<----------------------------|  { session_id, opening_narration, initial_state, ... }
    |                             |
    |  POST /game/action          |
    |  { session_id, action_type, action_id, action_text, ... }
    |---------------------------->|  GameLoop.process_action
    |                             |    1. get_state → load_snapshot(GameStateManager)
    |                             |    2. StateConverter.snapshot_to_game_state → RulesEngine.validate_action
    |                             |    3. build_narrator_prompt + GeminiClient.generate_structured(AIGameActionResponse)
    |                             |    4. apply resource_changes → resources.{name} modify
    |                             |    5. apply state_changes → _entity_path → set (player/npcs/crew_collective/locations)
    |                             |    6. increment_turn, _check_ending, update_state
    |<----------------------------|  GameActionResponse(narration, resource_changes, state_changes, ...)
    |                             |
    |  GET /game/state/{id}       |
    |---------------------------->|  GameLoop.get_state → get_state → StateConverter.snapshot_to_game_state
    |<----------------------------|  GameState
    |                             |
    |  POST /game/end-turn/{id}   |
    |---------------------------->|  GameLoop.advance_turn (decay, increment_turn, _check_ending, update_state)
    |<----------------------------|  TurnEndResponse(turn_number, narration, events_occurred, ...)
```

---

## 二、如何测试

### 1. 环境准备

- **MongoDB**：`settings.mongodb_uri`（默认 `mongodb://localhost:27017`），库名 `settings.mongodb_db_name`（默认 `odyssey7`）。
- **Gemini**：`GEMINI_API_KEY` 必填；未配置时 `process_action` 会走本地 fallback 叙事，不报错。
- **Config 路径**：`GameStateManager` / `SessionStateManager` 使用 `config_dir` 找 `state_variables.json`、`world_config.json`。  
  - Docker：`SessionStateManager` 使用 `/app/app/game_data`，在 `./backend:/app` 挂载下对应 `backend/app/game_data`。  
  - 本地直接跑：若未设置 `CONFIG_DIR` 或等价路径，`/app/app/game_data` 可能不存在，需在 `app` 所在目录或通过 `config_directory` 指向 `backend/app/game_data`。

### 2. 使用 `test_phase0.sh`（推荐）

```bash
# 1. 启动服务（任选其一）
docker-compose up -d backend    # 或用 uvicorn 本地跑 backend

# 2. 保证 Backend 在 http://localhost:8000，且 .env 中 GEMINI_API_KEY、MONGODB_URI 正确

# 3. 运行
./test_phase0.sh
```

`test_phase0.sh` 覆盖：健康检查、/docs、创建对局、取 state、执行 action、state 持久化、手动 end-turn、MongoDB 数据、部分数据模型。  
**注意**：Test 8 使用 `db.getSiblingDB('ai_rpg_game').sessions`，而 `settings.mongodb_db_name` 为 `odyssey7`，会查错库，需把脚本改为 `odyssey7` 或与 `MONGODB_DB_NAME` 一致。

### 3. 用 curl 做最小闭环

```bash
# 1. 建局
curl -s -X POST "http://localhost:8000/api/v1/game/start" \
  -H "Content-Type: application/json" \
  -d '{"player_name":"TestPlayer"}' | jq .

# 记下 session_id，代入下面 SESSION_ID

# 2. 取 state
curl -s "http://localhost:8000/api/v1/game/state/SESSION_ID" | jq .

# 3. 执行 action（action_type 须为 ActionCategory 枚举值，如 investigation）
curl -s -X POST "http://localhost:8000/api/v1/game/action" \
  -H "Content-Type: application/json" \
  -d '{"session_id":"SESSION_ID","action_type":"investigation","action_id":"check_systems","action_text":"I check the reactor"}' | jq .

# 4. 手动结束回合
curl -s -X POST "http://localhost:8000/api/v1/game/end-turn/SESSION_ID" | jq .
```

### 4. 后端单元 / 集成

```bash
cd backend
# 需先：pip install -r requirements.txt（含 pytest, pytest-asyncio 等）
pytest tests/ -v
```

- `tests/test_game_loop.py`：多为 `pass` 或 TODO，需接入 `GameLoop`、mock `get_state`/Gemini 等才能对 `process_action` / `advance_turn` 做断言。
- `conftest.py` 的 `sample_player_action` 使用 `action_type="freeform"`，而 `PlayerAction.action_type` 类型为 `ActionCategory`，无 `freeform`，在严格构造 `PlayerAction` 的测试中会 422，应改为如 `investigation`。

### 5. 前端

- `gameApi` 调用：`startGame`、`submitAction`、`getGameState`、`endTurn` 等已写，但请求/响应字段与后端存在命名和结构差异（见下「问题」）。
- 可 `npm run dev` 跑前端，用 `VITE_API_URL=http://localhost:8000/api/v1` 指向本地后端，再按界面操作做 E2E 式检查。

---

## 三、当前存在的问题

### 1. 配置与数据源不一致

| 问题 | 位置 | 说明 |
|------|------|------|
| **state_variables 格式** | `GameStateManager._initialize_state` | 期望 `state_config["state_variables"].get("resources", {})` 等；而 `state_variables.json` 是 `variables: [{ variable_path, initial_value, ... }]`。因此 `resources` / `ship_systems` / `crew_collective` 等不会被填入，开局 `state["resources"]` 为空。 |
| **world_config 结构** | `GameStateManager._initialize_state` | 使用 `if "world_config" in self.world_config` 且 `self.world_config["world_config"].get("locations", [])`；实际 `world_config.json` 顶层是 `locations: { id: {...} }`，没有 `world_config` 键，导致 `locations` 保持 `{}`。 |
| **StateConverter 与 resources 路径** | `StateConverter._convert_world` | 从 `state_dict["resources"]` 读取如 `oxygen_level`，并构造 `world.resources`。若 `GameStateManager` 的 `resources` 一直为空，`StateConverter` 会用默认值，与 `state_variables.json` 的 `world.resources.*.current` 设计不一致。 |

### 2. 路径与命名

| 问题 | 位置 | 说明 |
|------|------|------|
| **config_dir 写死** | `SessionStateManager`、`GameStateManager` | `config_dir="/app/app/game_data"`。Docker 下 `./backend:/app` 时 `app/game_data` 存在；本地非 Docker 常见为 `backend/app/game_data`，易导致 `FileNotFoundError`。应使用 `settings.config_directory` 或 `Path(__file__).parent / "game_data"` 等。 |
| **MongoDB 库名不一致** | `test_phase0.sh` | 脚本查 `ai_rpg_game.sessions`，应用使用 `odyssey7`。Test 8 会误报或无数据。 |

### 3. API 约定与前后端不一致

| 问题 | 后端 | 前端 / 文档 | 说明 |
|------|------|-------------|------|
| **End Turn 路径** | `POST /game/end-turn/{session_id}` | 前端 `POST /game/turn/end/{session_id}`；`API.md` 写 `POST /game/turn/end/{session_id}` | 前端与文档会 404，需统一为 `end-turn` 或 `turn/end` 之一。 |
| **Start 请求字段** | `player_name` | `gameApi.startGame` 送 `playerName` | Pydantic 默认不收 `playerName`，会 422 或缺字段；需前端改为 `player_name` 或后端做 alias。 |
| **Start 响应字段** | `session_id`, `opening_narration`, `initial_state`, `available_actions`, `oracle_message` | 部分类型/文档期望 `gameState`, `initialNarration` | 需在某一侧做映射（或后端 by_alias 出 camelCase）。 |
| **TurnEnd 响应** | `turn_number`, `narration`, `events_occurred`, `npc_actions_taken`, `state_summary`, `critical_alerts` | 类型期望 `gameState`, `turnSummary`, `events` | 结构不一致，前端无法直接沿用。 |
| **PlayerAction** | `session_id`, `action_type`(ActionCategory 枚举), `action_id`, `action_text`，蛇形 | 前端 `sessionId`, `actionType` 等 camelCase；`actionType` 若传 `"freeform"` 等非枚举值会 422 | 需要字段映射或校验前端枚举。 |
| **GameActionResponse** | 蛇形：`resource_changes`, `state_changes`, `npc_reactions`, `trigger_ending`, `ending_id`, `oracle_message`, `confidence_level` | 前端类型 camelCase | 若后端不转 camelCase，前端需按蛇形解析或做一次转换。 |

### 4. Save / Debug 路由

- Save：`SessionStateManager` 已有 `save_checkpoint` / `restore_checkpoint` / `get_checkpoints`，但 `/save/save`、`/save/saves`、`/save/load/{save_id}`、`/save/save/{save_id}` 未实现，全部 501/404。
- Debug：全部 501，且部分接口的 `game_loop` / `gemini_client` 已注入，但实现仍为占位。

### 5. 逻辑与实现细节

| 问题 | 位置 | 说明 |
|------|------|------|
| **action/stream** | `game.py` | 仅返回错误占位，未调用 `GameLoop.process_action_stream` 或任何流式生成。 |
| **get_available_actions** | `game.py` | 未根据 `player_actions.json`、state、location、资源、冷却等过滤，`actions` 恒为 `[]`。 |
| **advance_turn 的 decay** | `GameLoop.advance_turn` | 对 `oxygen_level`、`fuel_reserves`、`power_level`、`food_water` 写死 decay 量；未从 `state_variables.json` 的 `variables[].decay_rate` / `variable_path` 读。 |
| **Docker 前端 API 基地址** | `docker-compose.yml` | `VITE_API_URL=http://localhost:8000`，缺 `/api/v1`；`apiClient` 的 `baseURL` 为 `VITE_API_URL || 'http://localhost:8000/api/v1'`，会变成 `http://localhost:8000`，请求 `/game/start` 等会 404。应为 `http://localhost:8000/api/v1`。 |
| **EndingGenerator** | `ending_generator.py` | 调用 `self.gemini.generate_text`，而 `GeminiClient` 仅有 `generate` / `generate_structured` / `generate_stream` 等，方法名不一致，触发 ending 时若调用会 AttributeError。 |
| **conftest 的 sample_player_action** | `tests/conftest.py` | `action_type="freeform"` 不在 `ActionCategory`，构造 `PlayerAction` 会失败；应改为如 `investigation`。 |

### 6. 文档与实现不符

- `API.md`：`/game/turn/end`、请求/响应示例与当前后端不完全一致；Save 路径 `POST /game/save/{session_id}` 与实现 `POST /save/save` 不同。
- `ARCHITECTURE.md`：`POST /game/turn/end` 与 `POST /game/end-turn/{session_id}` 不一致。

---

## 四、建议的修复优先级

1. **高**：`GameStateManager` 按 `state_variables.json` 的 `variables` 和 `world_config.json` 的 `locations` 正确初始化 `resources`、`ship_systems`、`locations`，使 `StateConverter` 和 `GameLoop` 的 decay/apply 有可预期数据。
2. **高**：统一 `config_dir`（或 `config_directory`）来源，避免本地/Docker 下 `game_data` 找不到。
3. **高**：前后端 API 约定：  
   - 二选一：`/game/end-turn` 与 `/game/turn/end` 统一；  
   - `player_name` / `playerName`、`session_id` / `sessionId` 等至少在一侧做兼容（alias 或前端适配）；  
   - `TurnEndResponse`、`GameStartResponse` 与前端类型或文档对齐。
4. **中**：`test_phase0.sh` 中 MongoDB 库名改为 `odyssey7`（或与 `MONGODB_DB_NAME` 一致）；`conftest` 的 `action_type` 改为合法 `ActionCategory`。
5. **中**：`VITE_API_URL` 在 docker-compose 中设为 `http://localhost:8000/api/v1`；Save 路由对接 `save_checkpoint` / `restore_checkpoint`。
6. **低**：`action/stream` 接 `GameLoop.process_action_stream` 或等价实现；`get_available_actions` 按 state 过滤；`advance_turn` 的 decay 从 `state_variables` 读取；`EndingGenerator` 与 `GeminiClient` 方法对齐；Debug 路由逐步实现。

以上为当前「功能、Workflow、测试方式与已知问题」的整理；按此列表逐项修，可先把主流程与测试跑通，再补 Save、Stream、Debug 等。
