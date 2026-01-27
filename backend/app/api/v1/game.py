"""Game session endpoints."""

from typing import AsyncGenerator, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from app.api.schemas import (
    GameStartRequest,
    GameStartResponse,
    AvailableActionsResponse,
    TurnEndResponse,
)
from app.models.action import ActionDefinition, PlayerAction
from app.models.response import GameActionResponse
from app.models.game_state import GameState
from app.core.game_state_manager import GameStateManager
from app.core.session_state_manager import SessionStateManager
from app.utils.state_converter import StateConverter  # 👈 唯一新增的 import
from app.api.deps import get_session_manager
import json
from pathlib import Path
from pydantic import ValidationError

router = APIRouter()


@router.post(
    "/start",
    response_model=GameStartResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Start a new game",
    description="Creates a new game session with initialized NPCs, resources, and world state."
)
async def start_game(
    request: GameStartRequest,
    session_mgr: SessionStateManager = Depends(get_session_manager)
) -> GameStartResponse:
    """
    Start a new game session.

    - Creates new game state with player name
    - Generates initial NPCs with randomized personalities
    - Initializes ship systems and resources
    - Returns session ID and opening narration

    Args:
        request: Game start configuration
        session_mgr: Session state manager (injected)

    Returns:
        GameStartResponse with session_id, opening narration, and initial state

    Raises:
        HTTPException: If game creation fails
    """
    # Create new session in database
    session_id = await session_mgr.create_session(request.player_name)
    
    # Load initial state
    state_data = await session_mgr.get_state(session_id)
    
    # 👇 新增：Convert to GameState model for type safety
    game_state = StateConverter.snapshot_to_game_state(state_data, session_id)
    
    # TODO Phase 1: Generate opening narration with AI
    opening_narration = (
        f"You wake from cryosleep to flashing red lights and blaring alarms. "
        f"The ship's AI, ORACLE, greets you: 'Welcome back, {request.player_name}. "
        f"We have a situation.'"
    )
    
    # TODO Phase 1: Get initial available actions
    available_actions = ["explore_bridge", "check_systems", "talk_to_oracle"]
    
    return GameStartResponse(
        session_id=session_id,
        opening_narration=opening_narration,
        initial_state=game_state,  # 👈 修改：从 state_data 改为 game_state（现在是 GameState 对象）
        available_actions=available_actions,
        oracle_message="ALERT: MULTIPLE SYSTEM FAILURES DETECTED. CREW ASSISTANCE REQUIRED."
    )


@router.post(
    "/action",
    response_model=GameActionResponse,
    summary="Submit player action",
    description="Process a player action and return narration with state changes (non-streaming)."
)
async def submit_action(
    action: PlayerAction,
    session_mgr: SessionStateManager = Depends(get_session_manager)
) -> GameActionResponse:
    # 1) Load snapshot (doc["state"])
    try:
        snapshot = await session_mgr.get_state(action.session_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {action.session_id} not found"
        )

    # 2) Build GSM and load snapshot (NO wrapping)
    config_dir = Path(__file__).resolve().parents[2] / "game_data"  # app/game_data
    gsm = GameStateManager(config_dir=str(config_dir))
    gsm.load_snapshot(snapshot)

    # 3) Guard: ended?
    if gsm.get("game_meta.game_phase") == "ending":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Game has ended")

    # 4) Apply minimal action effect (Phase 1 stub)
    new_oxygen = _apply_oxygen_delta(gsm, -2.5)
    gsm.increment_turn()

    # 5) Save snapshot back
    new_snapshot = gsm.get_snapshot()
    ok = await session_mgr.update_state(action.session_id, new_snapshot)
    if not ok:
        raise HTTPException(status_code=500, detail="Failed to save game state")

    # 6) Response (保持你原有字段)
    narration_lines = [
        f"[System] Oxygen is now {new_oxygen:.1f}",
        f"[Player] action_id: {action.action_id}",
        f"[Player] action_text: {action.action_text}",
    ]

    return GameActionResponse(
        success=True,
        narration="\n".join(narration_lines),
        resource_changes=[],
        state_changes=[],
        npc_reactions=[],
        available_actions=["explore_location", "talk_to_npc", "rest", "check_systems"],
        mood="tense",
        trigger_ending=False,
        ending_id=None,
        oracle_message=None,
        confidence_level="high",
    )



def _apply_oxygen_delta(gsm: GameStateManager, delta: float) -> float:
    """Apply oxygen delta to GSM internal schema and clamp at 0. Return new value."""
    cur = gsm.get("world.resources.oxygen_level.current", 0.0)
    new_val = max(0.0, float(cur) - 2.5)
    if not isinstance(cur, (int, float)):
        # 如果当前结构被污染了，直接重置成 0 再算
        cur = 0.0
        gsm.set("world.resources.oxygen_level", cur, validate=False)

    new_val = max(0.0, float(cur) + float(delta))
    gsm.set("world.resources.oxygen_level.current", new_val, validate=False)
    return new_val

@router.post(
    "/action/stream",
    summary="Submit player action (streaming)",
    description="Process a player action with Server-Sent Events streaming for real-time narration.",
    responses={
        200: {
            "description": "Streaming narration response",
            "content": {"text/event-stream": {"example": "data: {chunk}\n\n"}}
        }
    }
)
async def submit_action_stream(
    action: PlayerAction,
    session_mgr: SessionStateManager = Depends(get_session_manager)
) -> StreamingResponse:
    """
    Submit a player action with SSE streaming response.

    Returns Server-Sent Events with chunked narration as the AI generates it.
    Final event includes complete state changes.

    Event format:
    ```
    data: {"type": "narration", "chunk": "You approach the reactor..."}

    data: {"type": "narration", "chunk": " The readings are critical."}

    data: {"type": "complete", "response": {...}}
    ```

    Args:
        action: Player action with session_id and action details
        session_mgr: Session state manager (injected)

    Returns:
        StreamingResponse with text/event-stream content

    Raises:
        HTTPException 404: If session not found
        HTTPException 400: If action is invalid
    """
    async def generate_events() -> AsyncGenerator[str, None]:
        """Generate SSE events for streaming response."""
        import json
        
        # TODO Phase 1: Implement streaming
        # For now, return error message
        yield f'data: {json.dumps({"type": "error", "message": "Streaming not yet implemented. Use /action endpoint."})}\n\n'
    
    return StreamingResponse(
        generate_events(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


@router.get("/state/{session_id}")
async def get_game_state(session_id: str, session_mgr: SessionStateManager = Depends(get_session_manager)):
    try:
        state_data = await session_mgr.get_state(session_id)
    except ValueError:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")

    try:
        return StateConverter.snapshot_to_game_state(state_data, session_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"StateConverter failed: {type(e).__name__}: {e}")


@router.get(
    "/actions/{session_id}",
    response_model=AvailableActionsResponse,
    summary="Get available actions",
    description="Get list of currently available actions based on game state, location, and conditions."
)
async def get_available_actions(
    session_id: str,
    session_mgr: SessionStateManager = Depends(get_session_manager)
) -> AvailableActionsResponse:
    # 1) Load snapshot
    try:
        snapshot = await session_mgr.get_state(session_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found"
        )

    # 2) Normalize state
    state = snapshot.get("state", snapshot)
    player = state.get("player", {})
    world = state.get("world", {})

    player_loc = player.get("location", "cryo_bay")
    phase = state.get("phase", state.get("game_meta", {}).get("game_phase", "intro"))

    # 3) Load action definitions
    game_data_dir = Path(__file__).resolve().parents[2] / "game_data"
    actions_file = game_data_dir / "player_actions.json"

    actions: list[ActionDefinition] = []
    action_ids: list[str] = []  # 用于 urgent_actions / 去重

    def _location_requirement_allows(req_loc: str | None) -> bool:
        if not req_loc:
            return True

        if req_loc == player_loc:
            return True
        if req_loc in player_loc or player_loc in req_loc:
            return True

        # intro 特例
        if phase == "intro" and req_loc == "command_bridge":
            return True

        return False

    if actions_file.exists():
        try:
            data = json.loads(actions_file.read_text(encoding="utf-8"))
            raw_actions = data.get("actions", []) if isinstance(data, dict) else []

            for a in raw_actions:
                if not isinstance(a, dict):
                    continue

                action_id = a.get("id")
                if not action_id:
                    continue

                req = a.get("requirements", {}) or {}
                req_loc = req.get("location")

                # location filter（兼容 string / list）
                if isinstance(req_loc, list):
                    if req_loc and not any(_location_requirement_allows(x) for x in req_loc if isinstance(x, str)):
                        continue
                else:
                    if not _location_requirement_allows(req_loc if isinstance(req_loc, str) else None):
                        continue

                # ✅ 关键：把 dict 转成 ActionDefinition（而不是把 id 字符串塞进 actions）
                try:
                    action_def = ActionDefinition.model_validate(a)
                except ValidationError:
                    # 如果 JSON 某条 action 缺字段导致校验失败，就跳过这一条，避免整个接口 500
                    continue

                actions.append(action_def)
                action_ids.append(action_id)

        except Exception:
            actions = []
            action_ids = []

    # 4) Fallback：如果 JSON 过滤后为空，至少给基础动作
    if not actions:
        # ⚠️ 这里的字段要匹配你 ActionDefinition 的必填项
        DEFAULT_ACTION_DEFS: list[dict] = [
            {"id": "explore_location", "name": "Explore", "description": "Explore the current area."},
            {"id": "talk_to_npc", "name": "Talk", "description": "Talk to someone nearby."},
            {"id": "rest", "name": "Rest", "description": "Take a short rest."},
        ]
        if phase == "intro":
            DEFAULT_ACTION_DEFS.append(
                {"id": "check_systems", "name": "Check Systems", "description": "Review ship systems."}
            )

        actions = [ActionDefinition.model_validate(x) for x in DEFAULT_ACTION_DEFS]
        action_ids = [x["id"] for x in DEFAULT_ACTION_DEFS]

    # 5) Hints / urgent actions
    context_hints: list[str] = []
    urgent_actions: list[str] = []

    oxygen = world.get("resources", {}).get("oxygen_level", {}).get("current")
    oxygen_critical = world.get("resources", {}).get("oxygen_level", {}).get("critical_threshold", 20)

    if isinstance(oxygen, (int, float)):
        if oxygen <= oxygen_critical:
            context_hints.append("Oxygen is critical — you must address life support NOW.")
            if "check_systems" in action_ids:
                urgent_actions.append("check_systems")
        else:
            context_hints.append("Oxygen is dropping — check life support soon.")

    context_hints.append("ORACLE seems to have more information to share.")

    # 6) 去重（按 id 保序）
    seen = set()
    dedup_actions: list[ActionDefinition] = []
    for a in actions:
        aid = getattr(a, "id", None)
        if not aid or aid in seen:
            continue
        seen.add(aid)
        dedup_actions.append(a)
    actions = dedup_actions

    # urgent_actions 去重并确保存在于 actions
    valid_ids = {a.id for a in actions}
    urgent_actions = [x for x in dict.fromkeys(urgent_actions) if x in valid_ids]

    return AvailableActionsResponse(
        actions=actions,
        context_hints=context_hints,
        urgent_actions=urgent_actions
    )


@router.post(
    "/end-turn/{session_id}",
    response_model=TurnEndResponse,
    summary="End current turn",
    description="Manually end the current turn, triggering world update, events, and NPC actions."
)
async def end_turn(
    session_id: str,
    session_mgr: SessionStateManager = Depends(get_session_manager)
) -> TurnEndResponse:
    # 1) Load snapshot
    try:
        snapshot = await session_mgr.get_state(session_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found"
        )

    # 2) Build GSM and load snapshot (NO wrapping)
    config_dir = Path(__file__).resolve().parents[2] / "game_data"
    gsm = GameStateManager(config_dir=str(config_dir))
    gsm.load_snapshot(snapshot)

    # 3) Guard: ended?
    if gsm.get("game_meta.game_phase") == "ending":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Game has ended")

    # 4) Turn tick (Phase 1 stub)
    before = gsm.get("world.resources.oxygen_level.current", 0)
    after = max(0.0, float(before) - 2.5)
    gsm.set("world.resources.oxygen_level.current", after, validate=False)
    gsm.increment_turn()

    # 5) Save snapshot back
    new_snapshot = gsm.get_snapshot()
    ok = await session_mgr.update_state(session_id, new_snapshot)
    if not ok:
        raise HTTPException(status_code=500, detail="Failed to save game state")

    # 6) Response
    return TurnEndResponse(
        events_occurred=[],
        npc_actions_taken=[],
        state_summary={
            "resources_changed": [f"oxygen_level: {before} -> {after}"],
            "turn_advanced": True,
        },
        narration="Time passes. The ship creaks ominously.",
        critical_alerts=[],
        turn_number=gsm.get("game_meta.current_turn"),
    )