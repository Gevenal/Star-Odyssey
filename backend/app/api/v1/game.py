"""Game session endpoints."""

from typing import AsyncGenerator, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from app.api.schemas import (
    GameStartRequest,
    GameStartResponse,
    AvailableActionsResponse,
    TurnEndResponse,
    EndingResponse,
    EndingStatistics,
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
from app.api.deps import get_session_manager, get_game_loop, get_gemini_client, get_game_data_loader
from app.game_data.loader import GameDataLoader
import logging

logger = logging.getLogger(__name__)
import json
from pathlib import Path
from pydantic import ValidationError

from app.core.game_state_manager import GameStateManager
from app.core.ending_generator import EndingGenerator

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
    session_mgr: SessionStateManager = Depends(get_session_manager),
    gemini_client=Depends(get_gemini_client)
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
        gemini_client: Gemini AI client (injected)

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
    
    # Generate dynamic opening narration with AI
    try:
        npc_names = list(game_state.npcs.keys())[:3] if game_state.npcs else []
        opening_prompt = f"""You are the narrator for a sci-fi survival game aboard the damaged spaceship Odyssey-7.

Generate an atmospheric opening narration for a new game. The player's name is "{request.player_name}".

Context:
- The player just woke from cryosleep
- The ship is in crisis (systems failing, alarms blaring)
- ORACLE is the ship's AI assistant
- Other crew members present: {', '.join(npc_names) if npc_names else 'unknown'}

Requirements:
- 2-3 sentences, atmospheric and immersive
- Include sensory details (sounds, lights, temperature)
- End with ORACLE greeting the player
- Keep it under 100 words

Write ONLY the narration, no quotes or labels."""

        opening_narration = await gemini_client.generate(
            prompt=opening_prompt,
            model="flash",  # Use faster model for startup
            temperature=0.8,
            max_tokens=150
        )
        opening_narration = opening_narration.strip()
    except Exception as e:
        # Fallback to static narration if AI fails
        print(f"[game.py] AI narration failed: {e}, using fallback")
        opening_narration = (
            f"You wake from cryosleep to flashing red lights and blaring alarms. "
            f"The ship's AI, ORACLE, greets you: 'Welcome back, {request.player_name}. "
            f"We have a situation.'"
        )
    
    # Available actions at game start
    available_actions = ["explore_bridge", "check_systems", "talk_to_oracle"]
    
    return GameStartResponse(
        session_id=session_id,
        opening_narration=opening_narration,
        initial_state=game_state,
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
    session_mgr: SessionStateManager = Depends(get_session_manager)
) -> GameActionResponse:
    """
    Submit a player action for processing.

    This endpoint:
    1. Validates the action via RulesEngine
    2. Generates AI narration via Gemini
    3. Validates AI output via AIOutputValidator (prevents AI from exceeding authority)
    4. Applies state changes
    5. Checks for game ending conditions
    6. Persists the updated state

    Args:
        action: Player action with session_id and action details
        game_loop: GameLoop dependency (injected)

    Returns:
        GameActionResponse with narration, state changes, and NPC reactions

    Raises:
        HTTPException 404: If session not found
        HTTPException 400: If action is invalid (fails rules validation)
        HTTPException 409: If game has already ended
    """
    try:
        response = await game_loop.process_action(action.session_id, action)
        return response
    except ValueError as e:
        error_msg = str(e)
        if "not found" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_msg
            )
        elif "ended" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=error_msg
            )
        else:
            # Rules validation failure or other ValueError
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process action: {str(e)}"
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
    game_loop=Depends(get_game_loop)
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
        game_loop: GameLoop dependency (injected)

    Returns:
        StreamingResponse with text/event-stream content

    Raises:
        HTTPException 404: If session not found
        HTTPException 400: If action is invalid
    """
    async def generate_events() -> AsyncGenerator[str, None]:
        """Generate SSE events for streaming response."""
        import json
        
        try:
            # First, process the full action to get the complete response
            full_response = await game_loop.process_action(action.session_id, action)
            
            # Stream narration chunks
            narration = full_response.narration
            import re
            chunks = re.split(r'(?<=[.!?])\s+', narration) if narration else []
            
            for chunk in chunks:
                if chunk.strip():
                    yield f'data: {json.dumps({"type": "narration", "chunk": chunk.strip()})}\n\n'
                    # Small delay for realistic streaming effect
                    import asyncio
                    await asyncio.sleep(0.05)
            
            # Send complete response (serialize Pydantic model)
            complete_data = {
                "type": "complete",
                "response": full_response.model_dump(by_alias=True)
            }
            yield f'data: {json.dumps(complete_data)}\n\n'
            
        except ValueError as e:
            error_msg = str(e)
            if "not found" in error_msg.lower():
                yield f'data: {json.dumps({"type": "error", "code": 404, "message": error_msg})}\n\n'
            elif "ended" in error_msg.lower():
                yield f'data: {json.dumps({"type": "error", "code": 409, "message": error_msg})}\n\n'
            else:
                yield f'data: {json.dumps({"type": "error", "code": 400, "message": error_msg})}\n\n'
        except Exception as e:
            yield f'data: {json.dumps({"type": "error", "code": 500, "message": f"Internal error: {str(e)}"})}\n\n'
    
    return StreamingResponse(
        generate_events(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
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
    description="Get list of currently available actions based on game state, location, and conditions using RulesEngine."
)
async def get_available_actions(
    session_id: str,
    session_mgr: SessionStateManager = Depends(get_session_manager),
    game_data_loader: GameDataLoader = Depends(get_game_data_loader)
) -> AvailableActionsResponse:
    """
    Get available actions filtered by RulesEngine.
    
    The RulesEngine checks each action's requirements against current game state:
    - Location requirements
    - Resource levels (oxygen, power, etc.)
    - Required items in inventory
    - NPC presence at location
    - Required flags
    - Health/stress thresholds
    - Cooldowns and one-time actions
    """
    from app.core.rules.engine import RulesEngine
    from app.utils.state_converter import StateConverter
    
    # 1) Load session state
    try:
        snapshot = await session_mgr.get_state(session_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found"
        )

    # 2) Convert to GameState object for RulesEngine
    try:
        game_state = StateConverter.snapshot_to_game_state(snapshot, session_id)
    except Exception as e:
        # Fallback: work with raw dict if conversion fails
        logger.warning(f"StateConverter failed: {e}, using raw state")
        game_state = None

    # 3) Load all action definitions from JSON
    game_data_dir = Path(__file__).resolve().parents[2] / "game_data"
    actions_file = game_data_dir / "player_actions.json"
    
    all_actions: list[ActionDefinition] = []
    
    if actions_file.exists():
        try:
            data = json.loads(actions_file.read_text(encoding="utf-8"))
            raw_actions = data.get("actions", []) if isinstance(data, dict) else []
            
            for a in raw_actions:
                if not isinstance(a, dict) or not a.get("id"):
                    continue
                try:
                    action_def = ActionDefinition.model_validate(a)
                    all_actions.append(action_def)
                except ValidationError as ve:
                    logger.debug(f"Skipping invalid action {a.get('id')}: {ve}")
                    continue
        except Exception as e:
            logger.error(f"Failed to load actions file: {e}")
            all_actions = []

    # 4) Use RulesEngine to filter available actions
    if game_state and all_actions:
        rules_engine = RulesEngine(game_data_loader)
        available_actions = rules_engine.filter_available_actions(all_actions, game_state)
        unavailable_reasons = rules_engine.get_action_unavailability_reasons(all_actions, game_state)
    else:
        # Fallback if no game_state: simple location-based filter
        state = snapshot.get("state", snapshot)
        player = state.get("player", {})
        player_loc = player.get("location", "cryo_bay")
        
        available_actions = []
        unavailable_reasons = {}
        
        for action_def in all_actions:
            req_loc = action_def.requirements.location
            if req_loc:
                allowed_locations = [loc.strip() for loc in req_loc.split(",")]
                if player_loc not in allowed_locations:
                    unavailable_reasons[action_def.id] = f"Requires location: {req_loc}"
                    continue
            available_actions.append(action_def)
    
    # 5) Fallback: if no actions available, provide basics
    if not available_actions:
        DEFAULT_ACTION_DEFS: list[dict] = [
            {"id": "explore_location", "name": "Explore Area", "category": "investigation", 
             "description": "Explore the current area."},
            {"id": "talk_to_npc", "name": "Talk to Crew", "category": "social_interaction",
             "description": "Talk to someone nearby."},
            {"id": "quick_rest", "name": "Take a Break", "category": "rest_recovery",
             "description": "Take a short rest."},
        ]
        available_actions = [ActionDefinition.model_validate(x) for x in DEFAULT_ACTION_DEFS]

    action_ids = [a.id for a in available_actions]
    
    # 6) Generate context hints and urgent actions based on state
    context_hints: list[str] = []
    urgent_actions: list[str] = []
    
    state = snapshot.get("state", snapshot)
    world = state.get("world", {})
    player = state.get("player", {})
    
    # Check resources for hints
    resources = world.get("resources", {})
    oxygen = resources.get("oxygen_level", {})
    oxygen_current = oxygen.get("current") if isinstance(oxygen, dict) else None
    oxygen_critical = oxygen.get("critical_threshold", 25) if isinstance(oxygen, dict) else 25
    
    if isinstance(oxygen_current, (int, float)):
        if oxygen_current <= oxygen_critical:
            context_hints.append("⚠️ CRITICAL: Oxygen levels dangerously low!")
            if "repair_life_support" in action_ids:
                urgent_actions.append("repair_life_support")
            elif "check_systems" in action_ids:
                urgent_actions.append("check_systems")
        elif oxygen_current <= 50:
            context_hints.append("Oxygen levels dropping — address life support soon.")
    
    power = resources.get("power_level", {})
    power_current = power.get("current") if isinstance(power, dict) else None
    if isinstance(power_current, (int, float)) and power_current <= 20:
        context_hints.append("⚠️ Power levels critical — many systems unavailable.")
        if "repair_reactor" in action_ids:
            urgent_actions.append("repair_reactor")
    
    # Check player health
    player_health = player.get("health", 100)
    if isinstance(player_health, (int, float)) and player_health <= 30:
        context_hints.append("You are badly injured — seek medical attention.")
        if "treat_injuries" in action_ids:
            urgent_actions.append("treat_injuries")
    
    # Check player stress
    player_stress = player.get("stress", 0)
    if isinstance(player_stress, (int, float)) and player_stress >= 80:
        context_hints.append("Stress is overwhelming — find time to rest.")
        if "rest" in action_ids:
            urgent_actions.append("rest")
    
    # Location-specific hints
    player_loc = player.get("location", "cryo_bay")
    if player_loc == "command_bridge":
        context_hints.append("You can access ORACLE and ship systems from here.")
    elif player_loc == "engineering":
        context_hints.append("Engineering bay has repair tools and diagnostics.")
    elif player_loc == "med_bay":
        context_hints.append("Medical supplies and treatment available here.")
    
    # Always add ORACLE hint
    if "access_oracle" in action_ids:
        context_hints.append("ORACLE may have information to share.")

    # 7) Deduplicate actions (preserve order)
    seen = set()
    dedup_actions: list[ActionDefinition] = []
    for a in available_actions:
        aid = getattr(a, "id", None)
        if not aid or aid in seen:
            continue
        seen.add(aid)
        dedup_actions.append(a)
    
    # Deduplicate urgent_actions and ensure they exist in available actions
    valid_ids = {a.id for a in dedup_actions}
    urgent_actions = [x for x in dict.fromkeys(urgent_actions) if x in valid_ids]

    return AvailableActionsResponse(
        actions=dedup_actions,
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
    session_mgr: SessionStateManager = Depends(get_session_manager)
) -> TurnEndResponse:
    """
    End the current turn and advance game time.

    This endpoint triggers:
    1. Resource decay (oxygen, fuel, power, food - rates from state_variables.json)
    2. NPC autonomous actions via NPCScheduler
    3. Environmental damage checks
    4. Mutiny/sacrifice opportunity checks
    5. Critical resource warnings
    6. Turn increment and game ending checks

    Args:
        session_id: Game session identifier
        game_loop: GameLoop dependency (injected)

    Returns:
        TurnEndResponse with events, NPC actions, narration, and critical alerts

    Raises:
        HTTPException 404: If session not found
        HTTPException 409: If game has already ended
    """
    try:
        result = await game_loop.advance_turn(session_id)
        return TurnEndResponse(
            events_occurred=result.get("events_occurred", []),
            npc_actions_taken=result.get("npc_actions_taken", []),
            state_summary=result.get("state_summary", {}),
            narration=result.get("narration", "Time passes."),
            critical_alerts=result.get("critical_alerts", []),
            turn_number=result.get("turn_number", 0),
        )
    except ValueError as e:
        error_msg = str(e)
        if "not found" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_msg
            )
        elif "ended" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=error_msg
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to advance turn: {str(e)}"
        )


@router.get(
    "/ending/{session_id}",
    response_model=EndingResponse,
    summary="Get ending narration",
    description="Generate the ending narration and summary based on the final game state."
)
async def get_ending(
    session_id: str,
    session_mgr: SessionStateManager = Depends(get_session_manager),
    gemini_client=Depends(get_gemini_client)
) -> EndingResponse:
    """
    Generate ending text for the final state.

    Returns:
        EndingResponse with title, narration, epilogue, and statistics
    """
    try:
        state_data = await session_mgr.get_state(session_id)
    except ValueError:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")

    try:
        game_state = StateConverter.snapshot_to_game_state(state_data, session_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"StateConverter failed: {type(e).__name__}: {e}")

    generator = EndingGenerator(gemini_client)
    try:
        ending = await generator.generate_ending(game_state)
        metrics = ending.get("statistics", {})
        stats = EndingStatistics(
            days_survived=metrics.get("days_survived", game_state.world.day),
            crew_survived=metrics.get("survivors", game_state.count_alive_npcs()),
            secrets_discovered=metrics.get("secrets_found", len(game_state.player.discovered_secrets)),
            player_alive=metrics.get("player_alive", game_state.player.health > 0),
            crew_morale=metrics.get("avg_morale", game_state.world.crew_morale),
            oracle_sentience=metrics.get("oracle_sentience", game_state.oracle_sentience_level),
        )
        return EndingResponse(
            ending_type=ending.get("ending_type", "mixed"),
            title=ending.get("title", "The End"),
            narration=ending.get("narration", "").strip(),
            survivor_fates=ending.get("survivor_fates", {}),
            epilogue=ending.get("epilogue", ""),
            statistics=stats,
        )
    except Exception as e:
        logger.exception(f"Ending generation failed: {e}")
        metrics = generator._analyze_final_state(game_state)
        ending_type = generator._determine_ending_type(metrics)
        title = generator._generate_title(ending_type, metrics)
        epilogue = generator._generate_epilogue(game_state, metrics, ending_type)
        narration = (
            f"After {metrics['days_survived']} days adrift, the crew's story reached its end. "
            f"{'You survived' if metrics['player_alive'] else 'You did not survive'}, "
            f"and {metrics['survivors']} crew members remained. "
            "The Odyssey-7 drifted on, marked forever by the choices made in the void."
        )
        stats = EndingStatistics(
            days_survived=metrics["days_survived"],
            crew_survived=metrics["survivors"],
            secrets_discovered=metrics["secrets_found"],
            player_alive=metrics["player_alive"],
            crew_morale=metrics["avg_morale"],
            oracle_sentience=metrics["oracle_sentience"],
        )
        return EndingResponse(
            ending_type=ending_type,
            title=title,
            narration=narration,
            survivor_fates={},
            epilogue=epilogue,
            statistics=stats,
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
    "/npc/{npc_id}/interrogate",
    response_model=NPCInterrogationResponse,
    summary="Interrogate NPC",
    description="Interrogate an NPC with intense questioning to extract information."
)
async def interrogate_npc(
    npc_id: str,
    request: NPCInterrogationRequest,
    session_mgr: SessionStateManager = Depends(get_session_manager),
    gemini_client = Depends(get_gemini_client)
) -> NPCInterrogationResponse:
    """
    Interrogate an NPC.

    Args:
        npc_id: NPC to interrogate
        request: Interrogation request
        session_mgr: Session state manager
        gemini_client: Gemini client for AI generation

    Returns:
        NPCInterrogationResponse with interrogation result
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
    
    if not npc.alive:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{npc.name} is not available"
        )
    
    # Interrogate
    from app.utils.npc_interrogation_manager import NPCInterrogationManager
    from app.core.game_state_manager import GameStateManager
    
    manager = NPCInterrogationManager(gemini_client=gemini_client)
    result = await manager.interrogate_npc(
        npc, request.question, game_state, request.interrogation_type
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
    
    return NPCInterrogationResponse(
        success=result["success"],
        response=result["response"],
        trust_change=result.get("trust_change", 0),
        information_revealed=result.get("information_revealed", [])
    )


@router.post(
    "/npc/{npc_id}/transfer-item",
    response_model=NPCItemTransferResponse,
    summary="Transfer item with NPC",
    description="NPC gives item to player or requests item from player."
)
async def transfer_item_with_npc(
    npc_id: str,
    request: NPCItemTransferRequest,
    session_mgr: SessionStateManager = Depends(get_session_manager)
) -> NPCItemTransferResponse:
    """
    Transfer item with NPC.

    Args:
        npc_id: NPC to interact with
        request: Item transfer request
        session_mgr: Session state manager

    Returns:
        NPCItemTransferResponse with transfer result
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
    
    if not npc.alive:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{npc.name} is not available"
        )
    
    # Transfer item
    from app.utils.npc_item_manager import NPCItemManager
    from app.core.game_state_manager import GameStateManager
    
    if request.transfer_type == "npc_gives":
        result = NPCItemManager.npc_give_item_to_player(
            npc, game_state.player, request.item_id
        )
    else:  # "player_gives"
        result = NPCItemManager.npc_request_item_from_player(
            npc, game_state.player, request.item_id
        )
    
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("reason", "Item transfer failed")
        )
    
    # Update state
    state_data = await session_mgr.get_state(request.session_id)
    gs = GameStateManager()
    gs.load_snapshot(state_data)
    
    # Update NPC inventory
    gs.set(f"npcs.{npc_id}.inventory", npc.inventory, validate=False)
    
    # Update player inventory
    gs.set("player.inventory", game_state.player.inventory, validate=False)
    
    # Update relationship
    if "player" in npc.relationships:
        rel = npc.relationships["player"]
        gs.set(f"npcs.{npc_id}.relationships.player.trust_level", rel.trust_level, validate=False)
        gs.set(f"npcs.{npc_id}.relationships.player.relationship_history", rel.relationship_history, validate=False)
    
    updated_snapshot = gs.get_snapshot()
    await session_mgr.update_state(request.session_id, updated_snapshot)
    
    trust_change = result.get("trust_increase", 0)
    
    return NPCItemTransferResponse(
        success=True,
        transfer_type=request.transfer_type,
        item_id=request.item_id,
        trust_change=trust_change,
        message=result.get("message", "")
    )


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