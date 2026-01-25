"""Game session endpoints."""

from typing import AsyncGenerator
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from app.api.schemas import (
    GameStartRequest,
    GameStartResponse,
    AvailableActionsResponse,
    TurnEndResponse,
)
from app.models.action import PlayerAction
from app.models.response import GameActionResponse
from app.models.game_state import GameState
from app.core.game_state_manager import GameStateManager
from app.core.session_state_manager import SessionStateManager
from app.utils.state_converter import StateConverter  # 👈 唯一新增的 import
from app.api.deps import get_session_manager

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
    """
    Submit a player action (non-streaming response).

    - Validates action against current game rules
    - Processes action through game loop
    - Applies state changes
    - Generates AI narration
    - Triggers NPC reactions
    - Checks for ending conditions

    Args:
        action: Player action with session_id and action details
        session_mgr: Session state manager (injected)

    Returns:
        GameActionResponse with narration and all state changes

    Raises:
        HTTPException 404: If session not found
        HTTPException 400: If action is invalid
        HTTPException 409: If game has ended
    """
    # 1. Load state from database
    try:
        state_data = await session_mgr.get_state(action.session_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {action.session_id} not found"
        )
    
    # 2. Instantiate GameStateManager (in-memory)
    game_state = GameStateManager()
    game_state.load_snapshot(state_data)
    
    # Check if game has ended
    game_over = game_state.get("game_meta.game_phase") == "ending"
    if game_over:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Game has ended"
        )
    
    # 3. TODO Phase 1: Create GameLoop and process action
    # For now, simulate state changes
    game_state.modify("resources.oxygen_level.current", -2.5)
    game_state.increment_turn()
    
    # TODO Phase 1: AI narration generation
    narration = [
        f"[System] Oxygen level decreased by 2.5%",
        f"[Player] Executed action: {action.action_type}"
    ]
    
    # 4. Save back to database
    snapshot = game_state.get_snapshot()
    save_success = await session_mgr.update_state(action.session_id, snapshot)
    
    # 5. Return results
    # 👇 保持原有的返回格式
    return GameActionResponse(
        success=True,  # 👈 添加这个字段（GameActionResponse 需要）
        narration="\n".join(narration),  # 👈 修改：从 list 改为 string
        resource_changes=[],  # 👈 添加这个字段
        state_changes=[],  # 👈 添加这个字段
        npc_reactions=[],  # 👈 添加这个字段
        available_actions=["explore_bridge", "check_systems"],
        mood="tense",
        trigger_ending=False,  # 👈 添加这个字段
        ending_id=None  # 👈 添加这个字段
    )


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


@router.get(
    "/state/{session_id}",
    response_model=GameState,  # 👈 修改：添加明确的返回类型
    summary="Get game state",
    description="Retrieve the current complete game state for a session."
)
async def get_game_state(
    session_id: str,
    session_mgr: SessionStateManager = Depends(get_session_manager)
) -> GameState:  # 👈 修改：添加返回类型注解
    """
    Get current game state for a session.

    Args:
        session_id: Game session identifier
        session_mgr: Session state manager (injected)

    Returns:
        Complete game state (as GameState model for type safety)

    Raises:
        HTTPException 404: If session not found
    """
    try:
        state_data = await session_mgr.get_state(session_id)
        
        # 👇 新增：Convert to GameState model
        game_state = StateConverter.snapshot_to_game_state(state_data, session_id)
        
        return game_state  # 👈 修改：返回 GameState 对象而不是字典
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found"
        )


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
    """
    Get list of currently available actions.

    Filters actions based on:
    - Player location
    - Player inventory
    - Resource levels
    - NPC presence
    - Quest/flag states
    - Action cooldowns

    Args:
        session_id: Game session identifier
        session_mgr: Session state manager (injected)

    Returns:
        AvailableActionsResponse with actions, hints, and urgent action IDs

    Raises:
        HTTPException 404: If session not found
    """
    # Verify session exists
    try:
        state_data = await session_mgr.get_state(session_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found"
        )
    
    # TODO Phase 1: Implement action filtering based on game state
    # For now, return basic actions
    return AvailableActionsResponse(
        actions=[],  # TODO: Parse from player_actions.json based on state
        context_hints=[
            "The oxygen levels are dropping - you should check life support",
            "ORACLE seems to have more information to share"
        ],
        urgent_actions=[]  # TODO: Determine based on resource levels
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
    """
    Manually end current turn and advance game state.

    Executes in order:
    1. World update (resource decay, system degradation)
    2. Random event generation and processing
    3. NPC autonomous actions
    4. Ending condition checks

    Args:
        session_id: Game session identifier
        session_mgr: Session state manager (injected)

    Returns:
        TurnEndResponse with events, NPC actions, and state summary

    Raises:
        HTTPException 404: If session not found
        HTTPException 409: If game has ended
    """
    # Load state
    try:
        state_data = await session_mgr.get_state(session_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found"
        )
    
    # Check if game has ended
    game_state = GameStateManager()
    game_state.load_snapshot(state_data)
    
    if game_state.get("game_meta.game_phase") == "ending":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Game has ended"
        )
    
    # TODO Phase 1: Implement turn advancement with GameLoop
    # For now, simulate basic turn changes
    game_state.modify("resources.oxygen_level.current", -2.5)
    game_state.increment_turn()
    
    # Save state
    snapshot = game_state.get_snapshot()
    await session_mgr.update_state(session_id, snapshot)
    
    return TurnEndResponse(
        events_occurred=[],  # TODO Phase 1
        npc_actions_taken=[],  # TODO Phase 1
        state_summary={
            "resources_changed": ["oxygen_level: -2.5"],
            "turn_advanced": True
        },
        narration="Time passes. The ship creaks ominously.",
        critical_alerts=[],  # TODO: Check resource thresholds
        turn_number=game_state.get("game_meta.current_turn")
    )