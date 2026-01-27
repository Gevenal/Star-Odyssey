"""Debug endpoints (development only)."""

import json
from typing import Any, Dict
from fastapi import APIRouter, Depends, HTTPException, status
from app.config import settings
from app.api.schemas import (
    DebugStateResponse,
    DebugSetVariableRequest,
    DebugTriggerEventRequest,
    DebugExplainRisksResponse,
)
from app.api.deps import get_session_manager, get_gemini_client, get_game_loop
from app.core.game_state_manager import GameStateManager
from app.utils.state_converter import StateConverter
from app.ai.prompts.debug_prompt import (
    build_debug_risk_analysis_prompt,
    extract_immediate_threats,
    extract_medium_term_risks,
    extract_long_term_concerns,
)

router = APIRouter()


def check_dev_only():
    """Dependency to ensure debug endpoints only work in development."""
    if settings.app_env != "development":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Debug endpoints are only available in development mode"
        )


@router.get(
    "/state/dump/{session_id}",
    response_model=DebugStateResponse,
    summary="[DEV] Dump full state",
    description="Development only: Get complete game state dump with internal metadata.",
    dependencies=[Depends(check_dev_only)]
)
async def dump_state(
    session_id: str,
    state_manager=Depends(get_session_manager)
) -> DebugStateResponse:
    """
    Dump full game state for debugging.

    Includes all internal state, flags, and metadata not normally exposed to the client.
    Useful for debugging state issues or understanding game progression.

    Args:
        session_id: Game session identifier
        state_manager: StateManager dependency

    Returns:
        DebugStateResponse with complete state dump

    Raises:
        HTTPException 403: If not in development mode
        HTTPException 404: If session not found
    """
    # TODO: Implement state dump
    # game_state = await state_manager.get_state(session_id)
    # if not game_state:
    #     raise HTTPException(
    #         status_code=status.HTTP_404_NOT_FOUND,
    #         detail=f"Session {session_id} not found"
    #     )

    # cache_data = await state_manager.get_from_cache(session_id)
    # internal_flags = await state_manager.get_internal_flags(session_id)

    # return DebugStateResponse(
    #     session_id=session_id,
    #     game_state=game_state,
    #     internal_flags=internal_flags,
    #     ai_context_size=calculate_context_size(game_state),
    #     cache_status={"cached": cache_data is not None, "ttl": ...}
    # )

    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="State dump not yet implemented"
    )


@router.post(
    "/state/set-variable",
    summary="[DEV] Set state variable",
    description="Development only: Manually set a specific state variable for testing.",
    dependencies=[Depends(check_dev_only)]
)
async def set_state_variable(
    request: DebugSetVariableRequest,
    state_manager=Depends(get_session_manager)
) -> Dict[str, Any]:
    """
    Manually set game state variable for testing.

    Allows directly modifying any state variable using dot notation.
    Useful for testing specific scenarios or edge cases.

    Examples:
    - `player.health` = 10 (set player health to critical)
    - `world.resources.oxygen_level.current` = 5.0 (simulate oxygen crisis)
    - `npcs.npc_captain.alive` = False (kill an NPC for testing)

    Args:
        request: Variable path and value to set
        state_manager: StateManager dependency

    Returns:
        Confirmation with old and new values

    Raises:
        HTTPException 403: If not in development mode
        HTTPException 404: If session not found
        HTTPException 400: If variable path is invalid
    """
    # TODO: Implement state variable setting
    # game_state = await state_manager.get_state(request.session_id)
    # if not game_state:
    #     raise HTTPException(
    #         status_code=status.HTTP_404_NOT_FOUND,
    #         detail=f"Session {request.session_id} not found"
    #     )

    # old_value = get_nested_value(game_state, request.variable_path)
    # set_nested_value(game_state, request.variable_path, request.value)
    # await state_manager.update_state(request.session_id, game_state)

    # return {
    #     "variable_path": request.variable_path,
    #     "old_value": old_value,
    #     "new_value": request.value,
    #     "updated": True
    # }

    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Set state variable not yet implemented"
    )


@router.post(
    "/trigger-event",
    summary="[DEV] Trigger event",
    description="Development only: Force trigger a random event, optionally skipping conditions.",
    dependencies=[Depends(check_dev_only)]
)
async def trigger_event(
    request: DebugTriggerEventRequest,
    game_loop=Depends(get_game_loop)
) -> Dict[str, Any]:
    """
    Force trigger a random event.

    Useful for testing event handling and outcomes without waiting for
    natural event conditions to be met.

    Args:
        request: Event ID and whether to skip trigger conditions
        game_loop: GameLoop dependency

    Returns:
        Event result and state changes

    Raises:
        HTTPException 403: If not in development mode
        HTTPException 404: If session or event not found
        HTTPException 400: If event conditions not met (when skip_conditions=False)
    """
    # TODO: Implement event triggering
    # game_state = await game_loop.get_state(request.session_id)
    # if not game_state:
    #     raise HTTPException(
    #         status_code=status.HTTP_404_NOT_FOUND,
    #         detail=f"Session {request.session_id} not found"
    #     )

    # event = event_registry.get_event(request.event_id)
    # if not event:
    #     raise HTTPException(
    #         status_code=status.HTTP_404_NOT_FOUND,
    #         detail=f"Event {request.event_id} not found"
    #     )

    # if not request.skip_conditions:
    #     can_trigger = await event_manager.check_conditions(event, game_state)
    #     if not can_trigger:
    #         raise HTTPException(
    #             status_code=status.HTTP_400_BAD_REQUEST,
    #             detail=f"Event {request.event_id} conditions not met"
    #         )

    # result = await event_manager.trigger_event(request.event_id, game_state)
    # return {
    #     "event_id": request.event_id,
    #     "triggered": True,
    #     "result": result,
    #     "state_changes": result.state_changes
    # }

    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Trigger event not yet implemented"
    )


@router.get(
    "/explain-risks/{session_id}",
    response_model=DebugExplainRisksResponse,
    summary="[DEV] AI risk analysis",
    description="Development only: Get AI-powered analysis of current dangers and risks.",
    dependencies=[Depends(check_dev_only)]
)
async def explain_risks(
    session_id: str,
    game_loop=Depends(get_game_loop),
    gemini_client=Depends(get_gemini_client)
) -> DebugExplainRisksResponse:
    """
    Get AI explanation of current risks and recommended actions.

    Uses Gemini to analyze the current game state and provide insights
    about immediate threats, medium-term risks, and strategic concerns.
    Useful for understanding game balance and testing AI analysis.

    Args:
        session_id: Game session identifier
        game_loop: GameLoop dependency
        gemini_client: GeminiClient dependency

    Returns:
        DebugExplainRisksResponse with risk analysis and recommendations

    Raises:
        HTTPException 403: If not in development mode
        HTTPException 404: If session not found
    """
    # Get game state
    try:
        state_data = await game_loop.state_manager.get_state(session_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found"
        )
    
    # Convert to GameState model
    gs = GameStateManager()
    gs.load_snapshot(state_data)
    snapshot = gs.get_snapshot()
    game_state = StateConverter.snapshot_to_game_state(snapshot, session_id)
    
    # Build analysis prompt
    analysis_prompt = build_debug_risk_analysis_prompt(game_state)
    
    # Get AI analysis
    try:
        ai_response_text = await gemini_client.generate(
            prompt=analysis_prompt,
            model="pro",
            temperature=0.7
        )
        
        # Parse JSON response
        # Try to extract JSON from markdown code blocks if present
        if "```json" in ai_response_text:
            json_start = ai_response_text.find("```json") + 7
            json_end = ai_response_text.find("```", json_start)
            ai_response_text = ai_response_text[json_start:json_end].strip()
        elif "```" in ai_response_text:
            json_start = ai_response_text.find("```") + 3
            json_end = ai_response_text.find("```", json_start)
            ai_response_text = ai_response_text[json_start:json_end].strip()
        
        ai_analysis = json.loads(ai_response_text)
        
        top_3_risks = ai_analysis.get("top_3_risks", [])
        hidden_cascades = ai_analysis.get("hidden_cascades", [])
        misleading_metrics = ai_analysis.get("misleading_metrics", [])
        recommended_actions = ai_analysis.get("recommended_actions", [])
        
    except Exception as e:
        # Fallback to rule-based extraction if AI fails
        top_3_risks = extract_immediate_threats(game_state)[:3]
        hidden_cascades = []
        misleading_metrics = []
        recommended_actions = []
        ai_response_text = f"AI analysis failed: {str(e)}. Using rule-based extraction."
    
    # Combine AI analysis with rule-based extraction
    immediate_threats = extract_immediate_threats(game_state)
    medium_term_risks = extract_medium_term_risks(game_state)
    long_term_concerns = extract_long_term_concerns(game_state)
    
    # Merge AI top_3_risks with immediate threats
    if top_3_risks:
        immediate_threats = list(set(immediate_threats + top_3_risks))[:5]
    
    return DebugExplainRisksResponse(
        session_id=session_id,
        risk_analysis=ai_response_text if 'ai_response_text' in locals() else "Analysis generated",
        immediate_threats=immediate_threats,
        medium_term_risks=medium_term_risks + hidden_cascades,
        long_term_concerns=long_term_concerns + misleading_metrics,
        recommended_actions=recommended_actions
    )


@router.post(
    "/ai/test-prompt",
    summary="[DEV] Test AI prompt",
    description="Development only: Test AI prompts directly without game context.",
    dependencies=[Depends(check_dev_only)]
)
async def test_ai_prompt(
    prompt: str,
    model: str = "pro",
    gemini_client=Depends(get_gemini_client)
) -> Dict[str, Any]:
    """
    Test AI prompt directly.

    Sends a raw prompt to Gemini and returns the response.
    Useful for testing prompt engineering and AI behavior.

    Args:
        prompt: Raw prompt text to send to AI
        model: Model to use ("pro" for narration, "flash" for NPCs)
        gemini_client: GeminiClient dependency

    Returns:
        AI response and metadata

    Raises:
        HTTPException 403: If not in development mode
        HTTPException 400: If invalid model specified
    """
    # TODO: Implement AI prompt testing
    # if model not in ["pro", "flash"]:
    #     raise HTTPException(
    #         status_code=status.HTTP_400_BAD_REQUEST,
    #         detail="Model must be 'pro' or 'flash'"
    #     )

    # if model == "pro":
    #     response = await gemini_client.generate_narration(prompt)
    # else:
    #     response = await gemini_client.generate_npc_response(prompt)

    # return {
    #     "prompt": prompt,
    #     "model": model,
    #     "response": response,
    #     "response_length": len(response)
    # }

    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="AI prompt testing not yet implemented"
    )
