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
from app.core.session_state_manager import SessionStateManager
from app.utils.state_converter import StateConverter
from app.api.deps import get_session_manager, get_game_loop

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
    game_loop=Depends(get_game_loop),
) -> GameActionResponse:
    """
    Submit a player action (non-streaming response).

    - Validates action against current game rules
    - Processes action through game loop (AI narration, state updates)
    - Applies state changes and checks ending conditions

    Raises:
        HTTPException 404: If session not found
        HTTPException 400: If action is invalid
        HTTPException 409: If game has ended
    """
    try:
        return await game_loop.process_action(action.session_id, action)
    except ValueError as e:
        msg = str(e)
        if "not found" in msg.lower():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=msg)
        if "game has ended" in msg.lower() or "ended" in msg.lower():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=msg)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)


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
    game_loop=Depends(get_game_loop),
) -> GameState:
    """
    Get current game state for a session.

    Raises:
        HTTPException 404: If session not found
    """
    try:
        return await game_loop.get_state(session_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e) or f"Session {session_id} not found",
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
    game_loop=Depends(get_game_loop),
) -> TurnEndResponse:
    """
    Manually end current turn: resource decay, increment, ending check.

    Raises:
        HTTPException 404: If session not found
        HTTPException 409: If game has ended
    """
    try:
        result = await game_loop.advance_turn(session_id)
        return TurnEndResponse(**result)
    except ValueError as e:
        msg = str(e)
        if "not found" in msg.lower():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=msg)
        if "ended" in msg.lower():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=msg)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)