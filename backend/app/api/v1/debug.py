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
    try:
        state_data = await state_manager.get_state(session_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found"
        )
    
    # Convert to GameState model
    game_state = StateConverter.snapshot_to_game_state(state_data, session_id)
    
    # Get cache status
    cache_data = await state_manager.get_from_cache(session_id) if state_manager.redis_cache else None
    
    # Extract internal flags from state
    internal_flags = {
        "turn": state_data.get("turn", 0),
        "game_phase": state_data.get("state", {}).get("game_meta", {}).get("game_phase", "unknown"),
        "ending_id": state_data.get("state", {}).get("game_meta", {}).get("ending_id"),
        "player_flags": state_data.get("state", {}).get("player", {}).get("flags", {}),
        "global_flags": state_data.get("state", {}).get("world", {}).get("global_flags", {}),
    }
    
    # Estimate AI context size (rough approximation)
    try:
        ai_context_size = len(json.dumps(state_data, default=str)) // 4  # ~4 chars per token
    except Exception:
        ai_context_size = 500  # fallback estimate
    
    return DebugStateResponse(
        session_id=session_id,
        game_state=game_state,
        internal_flags=internal_flags,
        ai_context_size=ai_context_size,
        cache_status={"cached": cache_data is not None, "redis_enabled": state_manager.redis_cache is not None}
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
    - `resources.oxygen_level` = 5.0 (simulate oxygen crisis)
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
    try:
        state_data = await state_manager.get_state(request.session_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {request.session_id} not found"
        )
    
    # Load into GameStateManager for easy path manipulation
    gs = GameStateManager()
    gs.load_snapshot(state_data)
    
    # Get old value
    try:
        old_value = gs.get(request.variable_path)
    except (KeyError, TypeError):
        old_value = None
    
    # Set new value
    try:
        gs.set(request.variable_path, request.value, validate=False)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid variable path '{request.variable_path}': {str(e)}"
        )
    
    # Save updated state
    snapshot = gs.get_snapshot()
    await state_manager.update_state(request.session_id, snapshot)
    
    return {
        "variable_path": request.variable_path,
        "old_value": old_value,
        "new_value": request.value,
        "updated": True
    }


@router.post(
    "/trigger-event",
    summary="[DEV] Trigger event",
    description="Development only: Force trigger a random event, optionally skipping conditions.",
    dependencies=[Depends(check_dev_only)]
)
async def trigger_event(
    request: DebugTriggerEventRequest,
    state_manager=Depends(get_session_manager),
    gemini_client=Depends(get_gemini_client)
) -> Dict[str, Any]:
    """
    Force trigger a random event.

    Generates and applies an event using AI based on the event_id hint.
    Useful for testing event handling and narrative outcomes.

    Args:
        request: Event ID (used as hint for AI generation) and skip_conditions flag
        state_manager: StateManager dependency
        gemini_client: GeminiClient dependency

    Returns:
        Event result with narration and state changes

    Raises:
        HTTPException 403: If not in development mode
        HTTPException 404: If session not found
    """
    try:
        state_data = await state_manager.get_state(request.session_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {request.session_id} not found"
        )
    
    # Load state
    gs = GameStateManager()
    gs.load_snapshot(state_data)
    game_state = StateConverter.snapshot_to_game_state(gs.get_snapshot(), request.session_id)
    
    # Generate event narration using AI
    event_prompt = f"""Generate a dramatic random event for a sci-fi survival game.

Event type hint: {request.event_id}
Player location: {game_state.player.location if game_state.player else 'bridge'}
Current turn: {state_data.get('turn', 0)}

Generate a short event (2-3 sentences) and suggest one state change.
Format your response as JSON:
{{
    "event_name": "Brief event title",
    "narration": "The dramatic event description...",
    "state_change": {{
        "path": "resources.oxygen_level",
        "delta": -5
    }}
}}"""

    try:
        ai_response = await gemini_client.generate(
            prompt=event_prompt,
            model="flash",
            temperature=0.9
        )
        
        # Parse AI response
        if "```json" in ai_response:
            json_start = ai_response.find("```json") + 7
            json_end = ai_response.find("```", json_start)
            ai_response = ai_response[json_start:json_end].strip()
        elif "```" in ai_response:
            json_start = ai_response.find("```") + 3
            json_end = ai_response.find("```", json_start)
            ai_response = ai_response[json_start:json_end].strip()
        
        event_data = json.loads(ai_response)
        
        # Apply state change if provided
        state_changes = []
        if "state_change" in event_data and event_data["state_change"]:
            change = event_data["state_change"]
            path = change.get("path", "")
            delta = change.get("delta", 0)
            
            if path and delta:
                try:
                    old_value = gs.get(path)
                    if isinstance(old_value, (int, float)):
                        new_value = old_value + delta
                        gs.set(path, new_value, validate=False)
                        state_changes.append({
                            "path": path,
                            "old_value": old_value,
                            "new_value": new_value
                        })
                except:
                    pass
        
        # Save updated state
        await state_manager.update_state(request.session_id, gs.get_snapshot())
        
        return {
            "event_id": request.event_id,
            "event_name": event_data.get("event_name", "Unknown Event"),
            "triggered": True,
            "narration": event_data.get("narration", "Something happened..."),
            "state_changes": state_changes
        }
        
    except Exception as e:
        # Fallback to simple event
        return {
            "event_id": request.event_id,
            "event_name": f"Debug Event: {request.event_id}",
            "triggered": True,
            "narration": f"A {request.event_id.replace('_', ' ')} event occurs on the ship.",
            "state_changes": [],
            "error": str(e)
        }


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
    temperature: float = 0.7,
    gemini_client=Depends(get_gemini_client)
) -> Dict[str, Any]:
    """
    Test AI prompt directly.

    Sends a raw prompt to Gemini and returns the response.
    Useful for testing prompt engineering and AI behavior.

    Args:
        prompt: Raw prompt text to send to AI
        model: Model to use ("pro" for narration, "flash" for NPCs)
        temperature: Temperature for generation (0.0-1.0)
        gemini_client: GeminiClient dependency

    Returns:
        AI response and metadata

    Raises:
        HTTPException 403: If not in development mode
        HTTPException 400: If invalid model specified
    """
    if model not in ["pro", "flash"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Model must be 'pro' or 'flash'"
        )
    
    try:
        response = await gemini_client.generate(
            prompt=prompt,
            model=model,
            temperature=temperature
        )
        
        return {
            "prompt": prompt[:200] + "..." if len(prompt) > 200 else prompt,
            "model": model,
            "temperature": temperature,
            "response": response,
            "response_length": len(response)
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI generation failed: {str(e)}"
        )
