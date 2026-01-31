"""Game session endpoints."""

from typing import AsyncGenerator, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from app.api.schemas import (
    GameStartRequest,
    GameStartResponse,
    AvailableActionsResponse,
    TurnEndResponse,
    NPCTalkRequest,
    NPCTalkResponse,
    NPCInterrogationRequest,
    NPCInterrogationResponse,
    NPCItemTransferRequest,
    NPCItemTransferResponse,
    AssignTaskRequest,
    AssignTaskResponse,
    MediateConflictRequest,
    MediateConflictResponse,
    BoostMoraleRequest,
    BoostMoraleResponse,
    FormAllianceRequest,
    FormAllianceResponse,
    ListConflictsResponse,
    ProvideTherapyRequest,
    ProvideTherapyResponse,
    PlayerCounselingRequest,
    PlayerCounselingResponse,
    InvestigateNPCRequest,
    InvestigateNPCResponse,
    ListSuspiciousNPCsResponse,
    GetNPCSkillsResponse,
)
from app.models.action import ActionDefinition, PlayerAction
from app.models.response import GameActionResponse
from app.models.game_state import GameState
from app.core.session_state_manager import SessionStateManager
from app.utils.state_converter import StateConverter
from app.api.deps import get_session_manager, get_game_loop, get_gemini_client
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
    - Generates initial NPCs with randomized personalities (via GameStateManager._initialize_state)
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
    # Note: NPCs are automatically generated during GameStateManager initialization
    # (see GameStateManager._initialize_state() which calls NPCGenerator.generate_full_crew())
    session_id = await session_mgr.create_session(request.player_name)
    
    # Load initial state (NPCs should already be generated and included)
    state_data = await session_mgr.get_state(session_id)
    
    # Convert to GameState model for type safety
    # This will include all generated NPCs in game_state.npcs
    game_state = StateConverter.snapshot_to_game_state(state_data, session_id)
    
    # Verify NPCs were generated (for debugging)
    if not game_state.npcs:
        print(f"[game.py] Warning: No NPCs found in initial state for session {session_id}")
    else:
        print(f"[game.py] Game started with {len(game_state.npcs)} NPCs: {list(game_state.npcs.keys())}")
    
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
    game_loop=Depends(get_game_loop),
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
    game_loop=Depends(get_game_loop),
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


@router.post(
    "/npc/{npc_id}/talk",
    response_model=NPCTalkResponse,
    summary="Talk to an NPC",
    description="Send a message to an NPC and receive their dialogue response."
)
async def talk_to_npc(
    npc_id: str,
    request: NPCTalkRequest,
    session_mgr: SessionStateManager = Depends(get_session_manager),
    gemini_client = Depends(get_gemini_client)
) -> NPCTalkResponse:
    """
    Talk to an NPC.

    - Loads game state
    - Creates NPCAgent for the NPC
    - Generates dialogue response using AI
    - Returns NPC's response with relationship info

    Args:
        npc_id: NPC identifier
        request: Talk request with session_id and message
        session_mgr: Session state manager
        gemini_client: Gemini client for AI generation

    Returns:
        NPCTalkResponse with NPC dialogue and relationship info

    Raises:
        HTTPException 404: If session or NPC not found
        HTTPException 400: If NPC is not available (dead, etc.)
    """
    # 1. Load game state
    try:
        state_data = await session_mgr.get_state(request.session_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {request.session_id} not found"
        )
    
    # 2. Convert to GameState
    game_state = StateConverter.snapshot_to_game_state(state_data, request.session_id)
    
    # 3. Get NPC
    npc = game_state.npcs.get(npc_id)
    if not npc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"NPC {npc_id} not found"
        )
    
    if not npc.alive:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{npc.name} is not available"
        )
    
    # 4. Create NPCAgent and generate dialogue
    from app.ai.agents.npc_agent import NPCAgent
    from app.utils.npc_secret_manager import NPCSecretManager
    from app.core.game_state_manager import GameStateManager
    
    agent = NPCAgent(gemini_client=gemini_client, npc_id=npc_id)
    
    try:
        dialogue = await agent.generate_dialogue(
            player_input=request.message,
            game_state=game_state
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate NPC dialogue: {str(e)}"
        )
    
    # 5. Check for quest giving (NPC may give quest during dialogue)
    from app.utils.npc_quest_manager import NPCQuestManager
    quest_given = None
    quest = NPCQuestManager.generate_quest(npc, game_state)
    if quest:
        # Add quest to player's active quests
        if quest.quest_id not in game_state.player.active_quests:
            game_state.player.active_quests.append(quest.quest_id)
            quest_given = quest.quest_id
            # Save quest to state
            state_data = await session_mgr.get_state(request.session_id)
            gs = GameStateManager()
            gs.load_snapshot(state_data)
            gs.set("player.active_quests", game_state.player.active_quests, validate=False)
            updated_snapshot = gs.get_snapshot()
            await session_mgr.update_state(request.session_id, updated_snapshot)
    
    # 6. Check for secret revelation after dialogue
    context = {
        "action_type": "dialogue",
        "player_message": request.message
    }
    revealed_secrets = NPCSecretManager.check_and_reveal_secrets(
        npc, game_state, context
    )
    
    # Update secrets in database if any were revealed
    if revealed_secrets:
        # Reload state to update
        state_data = await session_mgr.get_state(request.session_id)
        gs = GameStateManager()
        gs.load_snapshot(state_data)
        
        # Update secret known_by_player flags
        for secret in revealed_secrets:
            secret_idx = next(
                (i for i, s in enumerate(npc.secrets) if s.id == secret.id),
                None
            )
            if secret_idx is not None:
                gs.set(f"npcs.{npc_id}.secrets.{secret_idx}.known_by_player", True, validate=False)
        
        # Update player's discovered_secrets
        NPCSecretManager.update_player_discovered_secrets(
            game_state, revealed_secrets, npc_id
        )
        gs.set("player.discovered_secrets", game_state.player.discovered_secrets, validate=False)
        
        # Save updated state
        updated_snapshot = gs.get_snapshot()
        await session_mgr.update_state(request.session_id, updated_snapshot)
    
    # 6. Get relationship info
    relationship_level = 0
    if "player" in npc.relationships:
        relationship_level = npc.relationships["player"].trust_level
    
    disposition = npc.get_player_disposition().value if hasattr(npc.get_player_disposition(), 'value') else str(npc.get_player_disposition())
    
    # Include revealed secrets info in response
    revealed_secret_ids = [s.id for s in revealed_secrets] if revealed_secrets else []
    
    return NPCTalkResponse(
        npc_id=npc_id,
        npc_name=npc.name,
        dialogue=dialogue,
        relationship_level=relationship_level,
        disposition=disposition,
        quest_given=quest_given,
        secrets_revealed=revealed_secret_ids
    )


@router.get(
    "/npc/{npc_id}",
    summary="Get NPC information",
    description="Get detailed information about a specific NPC including personality, relationships, and current state."
)
async def get_npc_info(
    npc_id: str,
    session_id: str,
    session_mgr: SessionStateManager = Depends(get_session_manager)
):
    """
    Get NPC information.

    Args:
        npc_id: NPC identifier
        session_id: Game session ID
        session_mgr: Session state manager

    Returns:
        NPCState: Complete NPC state information

    Raises:
        HTTPException 404: If session or NPC not found
    """
    # 1. Load game state
    try:
        state_data = await session_mgr.get_state(session_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found"
        )
    
    # 2. Convert to GameState
    game_state = StateConverter.snapshot_to_game_state(state_data, session_id)
    
    # 3. Get NPC
    npc = game_state.npcs.get(npc_id)
    if not npc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"NPC {npc_id} not found"
        )
    
    return npc


@router.post(
    "/npc/{npc_id}/assign-task",
    response_model=AssignTaskResponse,
    summary="Assign task to NPC",
    description="Assign a specific task to an NPC. NPC may accept or refuse based on trust and compatibility."
)
async def assign_task_to_npc(
    npc_id: str,
    request: AssignTaskRequest,
    session_mgr: SessionStateManager = Depends(get_session_manager)
) -> AssignTaskResponse:
    """
    Assign a task to an NPC.

    Args:
        npc_id: NPC to assign task to
        request: Task assignment request
        session_mgr: Session state manager

    Returns:
        AssignTaskResponse with assignment result
    """
    # Load game state
    try:
        state_data = await session_mgr.get_state(request.session_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {request.session_id} not found"
        )
    
    game_state = StateConverter.snapshot_to_game_state(state_data, request.session_id)
    
    npc = game_state.npcs.get(npc_id)
    if not npc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"NPC {npc_id} not found"
        )
    
    # Get player trust level
    player_trust = 0
    if "player" in npc.relationships:
        player_trust = npc.relationships["player"].trust_level
    
    # Assign task
    from app.utils.npc_task_assignment import NPCTaskAssignment
    from app.core.game_state_manager import GameStateManager
    
    result = NPCTaskAssignment.assign_task_to_npc(
        npc, request.task_description, request.task_type, game_state, player_trust
    )
    
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("reason", "Task assignment failed")
        )
    
    # Update state
    state_data = await session_mgr.get_state(request.session_id)
    gs = GameStateManager()
    gs.load_snapshot(state_data)
    
    # Update NPC goals and activity
    gs.set(f"npcs.{npc_id}.goals", npc.goals, validate=False)
    gs.set(f"npcs.{npc_id}.current_activity", npc.current_activity, validate=False)
    
    # Update trust
    if "player" in npc.relationships:
        rel = npc.relationships["player"]
        gs.set(f"npcs.{npc_id}.relationships.player.trust_level", rel.trust_level, validate=False)
        gs.set(f"npcs.{npc_id}.relationships.player.relationship_history", rel.relationship_history, validate=False)
    
    updated_snapshot = gs.get_snapshot()
    await session_mgr.update_state(request.session_id, updated_snapshot)
    
    return AssignTaskResponse(
        success=True,
        npc_id=npc_id,
        npc_name=npc.name,
        task_description=request.task_description,
        trust_change=result.get("trust_change", 0),
        message=result.get("message", "")
    )


@router.get(
    "/conflicts",
    response_model=ListConflictsResponse,
    summary="List active conflicts",
    description="Get list of active conflicts between NPCs that can be mediated."
)
async def list_conflicts(
    session_id: str,
    session_mgr: SessionStateManager = Depends(get_session_manager)
) -> ListConflictsResponse:
    """
    List active conflicts between NPCs.

    Args:
        session_id: Game session ID
        session_mgr: Session state manager

    Returns:
        ListConflictsResponse with conflict list
    """
    # Load game state
    try:
        state_data = await session_mgr.get_state(session_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found"
        )
    
    game_state = StateConverter.snapshot_to_game_state(state_data, session_id)
    
    # Find conflicts
    from app.utils.npc_conflict_mediation import NPCConflictMediation
    conflicts = NPCConflictMediation.find_active_conflicts(game_state)
    
    return ListConflictsResponse(conflicts=conflicts)


@router.post(
    "/mediate-conflict",
    response_model=MediateConflictResponse,
    summary="Mediate conflict between NPCs",
    description="Attempt to mediate a conflict between two NPCs."
)
async def mediate_conflict(
    request: MediateConflictRequest,
    session_mgr: SessionStateManager = Depends(get_session_manager)
) -> MediateConflictResponse:
    """
    Mediate conflict between two NPCs.

    Args:
        request: Conflict mediation request
        session_mgr: Session state manager

    Returns:
        MediateConflictResponse with mediation result
    """
    # Load game state
    try:
        state_data = await session_mgr.get_state(request.session_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {request.session_id} not found"
        )
    
    game_state = StateConverter.snapshot_to_game_state(state_data, request.session_id)
    
    npc1 = game_state.npcs.get(request.npc1_id)
    npc2 = game_state.npcs.get(request.npc2_id)
    
    if not npc1:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"NPC {request.npc1_id} not found"
        )
    if not npc2:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"NPC {request.npc2_id} not found"
        )
    
    # Mediate conflict
    from app.utils.npc_conflict_mediation import NPCConflictMediation
    from app.core.game_state_manager import GameStateManager
    
    result = NPCConflictMediation.mediate_conflict(
        npc1, npc2, game_state, request.mediation_approach
    )
    
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("reason", "Mediation failed")
        )
    
    # Update state
    state_data = await session_mgr.get_state(request.session_id)
    gs = GameStateManager()
    gs.load_snapshot(state_data)
    
    # Update relationships
    if request.npc2_id in npc1.relationships:
        rel = npc1.relationships[request.npc2_id]
        gs.set(f"npcs.{request.npc1_id}.relationships.{request.npc2_id}.trust_level", rel.trust_level, validate=False)
        gs.set(f"npcs.{request.npc1_id}.relationships.{request.npc2_id}.relationship_history", rel.relationship_history, validate=False)
    if request.npc1_id in npc2.relationships:
        rel = npc2.relationships[request.npc1_id]
        gs.set(f"npcs.{request.npc2_id}.relationships.{request.npc1_id}.trust_level", rel.trust_level, validate=False)
        gs.set(f"npcs.{request.npc2_id}.relationships.{request.npc1_id}.relationship_history", rel.relationship_history, validate=False)
    
    # Update player relationships
    if "player" in npc1.relationships:
        rel = npc1.relationships["player"]
        gs.set(f"npcs.{request.npc1_id}.relationships.player.trust_level", rel.trust_level, validate=False)
    if "player" in npc2.relationships:
        rel = npc2.relationships["player"]
        gs.set(f"npcs.{request.npc2_id}.relationships.player.trust_level", rel.trust_level, validate=False)
    
    # Update morale
    if hasattr(game_state.world, 'crew_morale'):
        gs.set("world.crew_morale", game_state.world.crew_morale, validate=False)
    
    updated_snapshot = gs.get_snapshot()
    await session_mgr.update_state(request.session_id, updated_snapshot)
    
    return MediateConflictResponse(
        success=True,
        npc1_id=request.npc1_id,
        npc2_id=request.npc2_id,
        trust_improvement=result.get("trust_improvement"),
        morale_boost=result.get("morale_boost"),
        message=result.get("message", "")
    )


@router.post(
    "/boost-morale",
    response_model=BoostMoraleResponse,
    summary="Boost crew morale",
    description="Actively boost crew morale through various methods."
)
async def boost_morale(
    request: BoostMoraleRequest,
    session_mgr: SessionStateManager = Depends(get_session_manager)
) -> BoostMoraleResponse:
    """
    Boost crew morale.

    Args:
        request: Morale boost request
        session_mgr: Session state manager

    Returns:
        BoostMoraleResponse with boost result
    """
    # Load game state
    try:
        state_data = await session_mgr.get_state(request.session_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {request.session_id} not found"
        )
    
    game_state = StateConverter.snapshot_to_game_state(state_data, request.session_id)
    
    # Boost morale
    from app.utils.morale_boost_manager import MoraleBoostManager
    from app.core.game_state_manager import GameStateManager
    
    result = MoraleBoostManager.boost_morale(
        game_state, request.boost_method, request.target_npcs
    )
    
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("reason", "Morale boost failed")
        )
    
    # Update state
    state_data = await session_mgr.get_state(request.session_id)
    gs = GameStateManager()
    gs.load_snapshot(state_data)
    
    # Update morale
    gs.set("world.crew_morale", game_state.world.crew_morale, validate=False)
    
    # Update NPC stress and relationships
    for npc_info in result.get("affected_npcs", []):
        npc_id = npc_info["npc_id"]
        npc = game_state.npcs.get(npc_id)
        if npc:
            gs.set(f"npcs.{npc_id}.stress_level", npc.stress_level, validate=False)
            gs.set(f"npcs.{npc_id}.is_in_breakdown", npc.is_in_breakdown, validate=False)
            if "player" in npc.relationships:
                rel = npc.relationships["player"]
                gs.set(f"npcs.{npc_id}.relationships.player.trust_level", rel.trust_level, validate=False)
                gs.set(f"npcs.{npc_id}.relationships.player.relationship_history", rel.relationship_history, validate=False)
    
    updated_snapshot = gs.get_snapshot()
    await session_mgr.update_state(request.session_id, updated_snapshot)
    
    return BoostMoraleResponse(
        success=True,
        initial_morale=result["initial_morale"],
        new_morale=result["new_morale"],
        morale_boost=result["morale_boost"],
        affected_npcs=result.get("affected_npcs", []),
        message=result.get("message", "")
    )


@router.post(
    "/npc/{npc_id}/form-alliance",
    response_model=FormAllianceResponse,
    summary="Form alliance with NPC",
    description="Form an alliance with an NPC. Requires sufficient trust."
)
async def form_alliance_with_npc(
    npc_id: str,
    request: FormAllianceRequest,
    session_mgr: SessionStateManager = Depends(get_session_manager)
) -> FormAllianceResponse:
    """
    Form alliance with an NPC.

    Args:
        npc_id: NPC to form alliance with
        request: Alliance formation request
        session_mgr: Session state manager

    Returns:
        FormAllianceResponse with alliance result
    """
    # Load game state
    try:
        state_data = await session_mgr.get_state(request.session_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {request.session_id} not found"
        )
    
    game_state = StateConverter.snapshot_to_game_state(state_data, request.session_id)
    
    npc = game_state.npcs.get(npc_id)
    if not npc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"NPC {npc_id} not found"
        )
    
    # Form alliance
    from app.utils.npc_alliance_manager import NPCAllianceManager
    from app.core.game_state_manager import GameStateManager
    
    result = NPCAllianceManager.form_alliance(
        npc, game_state, request.alliance_type
    )
    
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("reason", "Alliance formation failed")
        )
    
    # Update state
    state_data = await session_mgr.get_state(request.session_id)
    gs = GameStateManager()
    gs.load_snapshot(state_data)
    
    # Update trust and relationship
    if "player" in npc.relationships:
        rel = npc.relationships["player"]
        gs.set(f"npcs.{npc_id}.relationships.player.trust_level", rel.trust_level, validate=False)
        gs.set(f"npcs.{npc_id}.relationships.player.relationship_history", rel.relationship_history, validate=False)
    
    # Update morale
    if hasattr(game_state.world, 'crew_morale'):
        gs.set("world.crew_morale", game_state.world.crew_morale, validate=False)
    
    updated_snapshot = gs.get_snapshot()
    await session_mgr.update_state(request.session_id, updated_snapshot)
    
    return FormAllianceResponse(
        success=True,
        npc_id=npc_id,
        npc_name=npc.name,
        alliance_type=result["alliance_type"],
        trust_boost=result["trust_boost"],
        new_trust_level=result["new_trust_level"],
        message=result.get("message", "")
    )


@router.post(
    "/npc/{therapist_npc_id}/provide-therapy/{patient_npc_id}",
    response_model=ProvideTherapyResponse,
    summary="Provide therapy to NPC",
    description="NPC provides therapy/counseling to help another NPC recover from breakdown."
)
async def provide_therapy(
    therapist_npc_id: str,
    patient_npc_id: str,
    request: ProvideTherapyRequest,
    session_mgr: SessionStateManager = Depends(get_session_manager)
) -> ProvideTherapyResponse:
    """
    Provide therapy to NPC.

    Args:
        therapist_npc_id: NPC providing therapy
        patient_npc_id: NPC receiving therapy
        request: Therapy request
        session_mgr: Session state manager

    Returns:
        ProvideTherapyResponse with therapy result
    """
    # Load game state
    try:
        state_data = await session_mgr.get_state(request.session_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {request.session_id} not found"
        )
    
    game_state = StateConverter.snapshot_to_game_state(state_data, request.session_id)
    
    therapist = game_state.npcs.get(therapist_npc_id)
    patient = game_state.npcs.get(patient_npc_id)
    
    if not therapist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Therapist NPC {therapist_npc_id} not found"
        )
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Patient NPC {patient_npc_id} not found"
        )
    
    # Provide therapy
    from app.utils.npc_recovery_manager import NPCRecoveryManager
    from app.core.game_state_manager import GameStateManager
    
    result = NPCRecoveryManager.provide_therapy(
        therapist, patient, game_state, request.therapy_type
    )
    
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("reason", "Therapy failed")
        )
    
    # Update state
    state_data = await session_mgr.get_state(request.session_id)
    gs = GameStateManager()
    gs.load_snapshot(state_data)
    
    # Update patient stress and breakdown state
    gs.set(f"npcs.{patient_npc_id}.stress_level", patient.stress_level, validate=False)
    gs.set(f"npcs.{patient_npc_id}.is_in_breakdown", patient.is_in_breakdown, validate=False)
    if result.get("recovered_from_breakdown"):
        gs.set(f"npcs.{patient_npc_id}.current_activity", None, validate=False)
    
    # Update relationship
    if patient_npc_id in therapist.relationships:
        rel = therapist.relationships[patient_npc_id]
        gs.set(f"npcs.{therapist_npc_id}.relationships.{patient_npc_id}.trust_level", rel.trust_level, validate=False)
        gs.set(f"npcs.{therapist_npc_id}.relationships.{patient_npc_id}.relationship_history", rel.relationship_history, validate=False)
    
    # Update morale
    if hasattr(game_state.world, 'crew_morale') and result.get("morale_boost", 0) > 0:
        gs.set("world.crew_morale", game_state.world.crew_morale, validate=False)
    
    updated_snapshot = gs.get_snapshot()
    await session_mgr.update_state(request.session_id, updated_snapshot)
    
    return ProvideTherapyResponse(
        success=True,
        therapist_name=therapist.name,
        patient_name=patient.name,
        stress_reduction=result["stress_reduction"],
        recovered_from_breakdown=result.get("recovered_from_breakdown", False),
        morale_boost=result.get("morale_boost", 0),
        message=result.get("message", "")
    )


@router.post(
    "/npc/{npc_id}/counsel",
    response_model=PlayerCounselingResponse,
    summary="Player provides counseling",
    description="Player provides counseling to help NPC recover from breakdown."
)
async def player_provide_counseling(
    npc_id: str,
    request: PlayerCounselingRequest,
    session_mgr: SessionStateManager = Depends(get_session_manager)
) -> PlayerCounselingResponse:
    """
    Player provides counseling to NPC.

    Args:
        npc_id: NPC to counsel
        request: Counseling request
        session_mgr: Session state manager

    Returns:
        PlayerCounselingResponse with counseling result
    """
    # Load game state
    try:
        state_data = await session_mgr.get_state(request.session_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {request.session_id} not found"
        )
    
    game_state = StateConverter.snapshot_to_game_state(state_data, request.session_id)
    
    npc = game_state.npcs.get(npc_id)
    if not npc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"NPC {npc_id} not found"
        )
    
    # Provide counseling
    from app.utils.npc_recovery_manager import NPCRecoveryManager
    from app.core.game_state_manager import GameStateManager
    
    result = NPCRecoveryManager.player_provide_counseling(
        npc, game_state, request.counseling_approach
    )
    
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("reason", "Counseling failed")
        )
    
    # Update state
    state_data = await session_mgr.get_state(request.session_id)
    gs = GameStateManager()
    gs.load_snapshot(state_data)
    
    # Update NPC stress and breakdown
    gs.set(f"npcs.{npc_id}.stress_level", npc.stress_level, validate=False)
    gs.set(f"npcs.{npc_id}.is_in_breakdown", npc.is_in_breakdown, validate=False)
    
    # Update relationship
    if "player" in npc.relationships:
        rel = npc.relationships["player"]
        gs.set(f"npcs.{npc_id}.relationships.player.trust_level", rel.trust_level, validate=False)
        gs.set(f"npcs.{npc_id}.relationships.player.relationship_history", rel.relationship_history, validate=False)
    
    # Update morale
    if hasattr(game_state.world, 'crew_morale') and result.get("morale_boost", 0) > 0:
        gs.set("world.crew_morale", game_state.world.crew_morale, validate=False)
    
    updated_snapshot = gs.get_snapshot()
    await session_mgr.update_state(request.session_id, updated_snapshot)
    
    return PlayerCounselingResponse(
        success=True,
        npc_name=npc.name,
        stress_reduction=result["stress_reduction"],
        recovered_from_breakdown=result.get("recovered_from_breakdown", False),
        trust_increase=result.get("trust_increase", 0),
        message=result.get("message", "")
    )


@router.get(
    "/suspicious-npcs",
    response_model=ListSuspiciousNPCsResponse,
    summary="List suspicious NPCs",
    description="Get list of NPCs showing suspicious behavior patterns."
)
async def list_suspicious_npcs(
    session_id: str,
    session_mgr: SessionStateManager = Depends(get_session_manager)
) -> ListSuspiciousNPCsResponse:
    """
    List suspicious NPCs.

    Args:
        session_id: Game session ID
        session_mgr: Session state manager

    Returns:
        ListSuspiciousNPCsResponse with suspicious NPCs
    """
    # Load game state
    try:
        state_data = await session_mgr.get_state(session_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found"
        )
    
    game_state = StateConverter.snapshot_to_game_state(state_data, session_id)
    
    # Check for suspicious behavior
    from app.utils.npc_investigation_manager import NPCInvestigationManager
    suspicious_npcs = NPCInvestigationManager.check_suspicious_behavior(game_state)
    
    return ListSuspiciousNPCsResponse(suspicious_npcs=suspicious_npcs)


@router.post(
    "/npc/{npc_id}/investigate",
    response_model=InvestigateNPCResponse,
    summary="Investigate NPC",
    description="Investigate an NPC for suspicious behavior or background information."
)
async def investigate_npc(
    npc_id: str,
    request: InvestigateNPCRequest,
    session_mgr: SessionStateManager = Depends(get_session_manager)
) -> InvestigateNPCResponse:
    """
    Investigate an NPC.

    Args:
        npc_id: NPC to investigate
        request: Investigation request
        session_mgr: Session state manager

    Returns:
        InvestigateNPCResponse with investigation results
    """
    # Load game state
    try:
        state_data = await session_mgr.get_state(request.session_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {request.session_id} not found"
        )
    
    game_state = StateConverter.snapshot_to_game_state(state_data, request.session_id)
    
    npc = game_state.npcs.get(npc_id)
    if not npc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"NPC {npc_id} not found"
        )
    
    # Investigate
    from app.utils.npc_investigation_manager import NPCInvestigationManager
    from app.core.game_state_manager import GameStateManager
    
    result = NPCInvestigationManager.investigate_npc(
        npc, game_state, request.investigation_type, request.investigation_method
    )
    
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("reason", "Investigation failed")
        )
    
    # Update state
    state_data = await session_mgr.get_state(request.session_id)
    gs = GameStateManager()
    gs.load_snapshot(state_data)
    
    # Update relationship
    if "player" in npc.relationships:
        rel = npc.relationships["player"]
        gs.set(f"npcs.{npc_id}.relationships.player.trust_level", rel.trust_level, validate=False)
        gs.set(f"npcs.{npc_id}.relationships.player.relationship_history", rel.relationship_history, validate=False)
    
    updated_snapshot = gs.get_snapshot()
    await session_mgr.update_state(request.session_id, updated_snapshot)
    
    return InvestigateNPCResponse(
        success=True,
        npc_name=npc.name,
        findings=result.get("findings", []),
        trust_change=result.get("trust_change", 0),
        message=result.get("message", "")
    )


@router.get(
    "/npc/{npc_id}/skills",
    response_model=GetNPCSkillsResponse,
    summary="Get NPC skills",
    description="Get NPC skill levels and summary."
)
async def get_npc_skills(
    npc_id: str,
    session_id: str,
    session_mgr: SessionStateManager = Depends(get_session_manager)
) -> GetNPCSkillsResponse:
    """
    Get NPC skills.

    Args:
        npc_id: NPC to check
        session_id: Game session ID
        session_mgr: Session state manager

    Returns:
        GetNPCSkillsResponse with NPC skills
    """
    # Load game state
    try:
        state_data = await session_mgr.get_state(session_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found"
        )
    
    game_state = StateConverter.snapshot_to_game_state(state_data, session_id)
    
    npc = game_state.npcs.get(npc_id)
    if not npc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"NPC {npc_id} not found"
        )
    
    # Get skills summary
    from app.utils.npc_skills_manager import NPCSkillsManager
    summary = NPCSkillsManager.get_npc_skill_summary(npc)
    
    return GetNPCSkillsResponse(
        npc_id=npc.id,
        npc_name=npc.name,
        skills=summary["skills"],
        primary_skills=summary["primary_skills"],
        average_skill_level=summary["average_skill_level"]
    )