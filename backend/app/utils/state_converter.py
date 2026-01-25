"""
State Converter - Convert between dict and Pydantic models
Fully compatible with all model definitions in backend/app/models/
"""
from typing import Dict, Any, List
from app.models.game_state import GameState
from app.models.player import PlayerState
from app.models.world import WorldState
from app.models.npc import NPCState, PersonalityTraits, NPCRelationship, NPCSecret
from app.models.resources import ResourceLevels, ResourceLevel, ShipSystems, SystemIntegrity
from app.models.location import LocationState
from app.models.enums import GamePhase, TurnPhase, Atmosphere


class StateConverter:
    """
    Convert between GameStateManager's dict format and Pydantic models.
    
    This bridges the gap between:
    - GameStateManager (uses nested dicts for flexibility and speed)
    - API responses (uses typed Pydantic models for validation)
    """
    
    @staticmethod
    def snapshot_to_game_state(snapshot: Dict[str, Any], session_id: str) -> GameState:
        """
        Convert GameStateManager snapshot to GameState Pydantic model.
        
        Args:
            snapshot: Dict from GameStateManager.get_snapshot()
                Format: {"state": {...}, "turn": int, "turn_history": [...]}
            session_id: Session identifier
            
        Returns:
            GameState: Fully validated Pydantic model
        """
        state_dict = snapshot.get("state", {})
        
        # Convert player
        player = StateConverter._convert_player(state_dict.get("player", {}))
        
        # Convert NPCs
        npcs = StateConverter._convert_npcs(state_dict.get("npcs", {}))
        
        # Convert world (includes resources and ship_systems)
        world = StateConverter._convert_world(
            state_dict.get("world", {}),
            state_dict.get("resources", {}),
            state_dict.get("ship_systems", {})
        )
        
        # Extract game metadata
        game_meta = state_dict.get("game_meta", {})
        
        # Create GameState
        return GameState(
            session_id=session_id,
            phase=GamePhase(game_meta.get("game_phase", "intro")),
            current_turn_phase=TurnPhase(game_meta.get("current_turn_phase", "player_turn")),
            player=player,
            npcs=npcs,
            world=world,
            turn_count=max(1, game_meta.get("current_turn", 0)),  # Ensure >= 1
            history=snapshot.get("turn_history", []),
            oracle_sentience_level=state_dict.get("oracle_sentience_level", 1),
            ending_triggered=game_meta.get("ending_triggered")
        )
    
    @staticmethod
    def _convert_player(player_dict: Dict[str, Any]) -> PlayerState:
        """Convert player dict to PlayerState model."""
        return PlayerState(
            name=player_dict.get("name", "Unknown"),
            health=player_dict.get("health", 100),
            stress=player_dict.get("stress", 0),
            radiation_exposure=player_dict.get("radiation_exposure", 0.0),
            location=player_dict.get("location", "cryo_bay"),
            inventory=player_dict.get("inventory", []),
            reputation=player_dict.get("reputation", {}),
            discovered_secrets=player_dict.get("discovered_secrets", []),
            completed_actions=player_dict.get("completed_actions", []),
            flags=player_dict.get("flags", {})
        )
    
    @staticmethod
    def _convert_npcs(npcs_dict: Dict[str, Any]) -> Dict[str, NPCState]:
        """Convert NPCs dict to Dict[str, NPCState]."""
        npcs = {}
        
        for npc_id, npc_data in npcs_dict.items():
            # Convert personality
            personality_data = npc_data.get("personality", {})
            
            # Handle both simple dict and nested structure
            if "core_value" in personality_data:
                # Simple format: {core_value: "duty", social_style: "authoritative", ...}
                personality = PersonalityTraits(
                    core_value=personality_data.get("core_value", "survival"),
                    social_style=personality_data.get("social_style", "neutral"),
                    stress_response=personality_data.get("stress_response", "analytical"),
                    decision_making=personality_data.get("decision_making", "logical"),
                    morality=personality_data.get("morality", "pragmatic"),
                    quirks=personality_data.get("quirks", [])
                )
            else:
                # Nested format: {core_values: {name: "duty", ...}, social_style: {name: "authoritative", ...}}
                personality = PersonalityTraits(
                    core_value=personality_data.get("core_values", {}).get("name", "survival"),
                    social_style=personality_data.get("social_style", {}).get("name", "neutral"),
                    stress_response=personality_data.get("stress_response", {}).get("name", "analytical"),
                    decision_making=personality_data.get("decision_making", {}).get("name", "logical"),
                    morality=personality_data.get("morality", {}).get("name", "pragmatic"),
                    quirks=personality_data.get("quirks", [])
                )
            
            # Convert relationships
            relationships = {}
            for rel_key, rel_data in npc_data.get("relationships", {}).items():
                if isinstance(rel_data, dict):
                    relationships[rel_key] = NPCRelationship(
                        target_npc_id=rel_data.get("target_npc_id", rel_key),
                        trust_level=rel_data.get("trust_level", 0),
                        relationship_history=rel_data.get("relationship_history", [])
                    )
                elif isinstance(rel_data, (int, float)):
                    # Simple format: just trust level
                    relationships[rel_key] = NPCRelationship(
                        target_npc_id=rel_key,
                        trust_level=int(rel_data),
                        relationship_history=[]
                    )
            
            # Convert secrets
            secrets_list = []
            for secret_data in npc_data.get("secrets", []):
                if isinstance(secret_data, dict):
                    secrets_list.append(NPCSecret(
                        id=secret_data.get("id", "unknown_secret"),
                        content=secret_data.get("content", ""),
                        known_by_player=secret_data.get("known_by_player", False),
                        reveal_condition=secret_data.get("reveal_condition")
                    ))
                elif isinstance(secret_data, str):
                    # Simple format: just secret ID or content
                    secrets_list.append(NPCSecret(
                        id=secret_data,
                        content=secret_data,
                        known_by_player=False,
                        reveal_condition=None
                    ))
            
            # Create NPC State
            npcs[npc_id] = NPCState(
                id=npc_id,
                name=npc_data.get("name", "Unknown NPC"),
                role=npc_data.get("role", "Crew Member"),
                location=npc_data.get("location", "unknown"),
                alive=npc_data.get("alive", True),
                health=npc_data.get("health", 100),
                stress_level=npc_data.get("stress_level", 30),
                personality=personality,
                relationships=relationships,
                goals=npc_data.get("goals", []),
                secrets=secrets_list,
                hidden_agenda=npc_data.get("hidden_agenda"),
                current_activity=npc_data.get("current_activity")
            )
        
        return npcs
    
    @staticmethod
    def _convert_world(
        world_dict: Dict[str, Any],
        resources_dict: Dict[str, Any],
        systems_dict: Dict[str, Any]
    ) -> WorldState:
        """Convert world dict to WorldState model."""
        
        # Helper: Convert resource data (handles both number and dict formats)
        def make_resource_level(res_data) -> ResourceLevel:
            """Convert resource data to ResourceLevel object."""
            if isinstance(res_data, (int, float)):
                # Simple format: just a number (e.g., 100.0)
                return ResourceLevel(
                    current=float(res_data),
                    max=100.0,
                    min=0.0,
                    critical_threshold=20.0,
                    decay_rate=0.0
                )
            elif isinstance(res_data, dict):
                # Detailed format: full object
                return ResourceLevel(
                    current=res_data.get("current", 100.0),
                    max=res_data.get("max", 100.0),
                    min=res_data.get("min", 0.0),
                    critical_threshold=res_data.get("critical_threshold", 20.0),
                    decay_rate=res_data.get("decay_rate", 0.0)
                )
            else:
                # Default values
                return ResourceLevel(
                    current=100.0,
                    max=100.0,
                    min=0.0,
                    critical_threshold=20.0,
                    decay_rate=0.0
                )
        
        # Convert resources
        resources = ResourceLevels(
            oxygen_level=make_resource_level(resources_dict.get("oxygen_level", 85.0)),
            fuel_reserves=make_resource_level(resources_dict.get("fuel_reserves", 60.0)),
            power_level=make_resource_level(resources_dict.get("power_level", 75.0)),
            medical_supplies=make_resource_level(resources_dict.get("medical_supplies", 50.0)),
            food_water=make_resource_level(resources_dict.get("food_supply", resources_dict.get("food_water", 70.0))),
            repair_materials=make_resource_level(resources_dict.get("spare_parts", resources_dict.get("repair_materials", 40.0)))
        )
        
        # Helper: Convert system integrity (handles both number and dict formats)
        def make_system_integrity(sys_data) -> SystemIntegrity:
            """Convert system data to SystemIntegrity object."""
            if isinstance(sys_data, (int, float)):
                # Simple format: just integrity value
                return SystemIntegrity(
                    integrity=float(sys_data),
                    operational=sys_data > 25.0,
                    degradation_rate=0.5
                )
            elif isinstance(sys_data, dict):
                # Detailed format: full object
                return SystemIntegrity(
                    integrity=sys_data.get("integrity", 100.0),
                    operational=sys_data.get("operational", True),
                    degradation_rate=sys_data.get("degradation_rate", 0.5)
                )
            else:
                # Default values
                return SystemIntegrity(
                    integrity=100.0,
                    operational=True,
                    degradation_rate=0.5
                )
        
        # Convert ship systems (note the exact field names from ShipSystems model)
        ship_systems = ShipSystems(
            reactor_integrity=make_system_integrity(systems_dict.get("reactor_integrity", 80.0)),
            hull_integrity=make_system_integrity(systems_dict.get("hull_integrity", 65.0)),
            life_support_efficiency=make_system_integrity(systems_dict.get("life_support_efficiency", systems_dict.get("life_support_integrity", 75.0))),
            navigation_systems=make_system_integrity(systems_dict.get("navigation_systems", systems_dict.get("navigation_integrity", 55.0))),
            communications_array=make_system_integrity(systems_dict.get("communications_array", systems_dict.get("communications_integrity", 30.0))),
            escape_pods_ready=systems_dict.get("escape_pods_ready", 6)
        )
        
        # Convert location states
        location_states = {}
        for loc_id, loc_data in world_dict.get("location_states", {}).items():
            if isinstance(loc_data, dict):
                location_states[loc_id] = LocationState(
                    is_sealed=loc_data.get("is_sealed", True),
                    atmosphere=Atmosphere(loc_data.get("atmosphere", "normal")),
                    power_available=loc_data.get("power_available", True),
                    current_hazards=loc_data.get("hazards", loc_data.get("current_hazards", []))
                )
        
        # Calculate time (could be in world_dict or game_meta)
        game_meta = world_dict.get("game_meta", {})
        day = world_dict.get("day", game_meta.get("current_day", 1))
        hour = world_dict.get("hour", game_meta.get("current_hour", 0))
        
        # Format time_of_day
        time_of_day = world_dict.get("time_of_day", f"{hour:02d}:00")
        
        # Calculate turn (2 hours per turn, 12 turns per day)
        turn = world_dict.get("turn", (hour // 2) + 1 if hour > 0 else 1)
        
        return WorldState(
            day=day,
            turn=turn,
            time_of_day=time_of_day,
            resources=resources,
            ship_systems=ship_systems,
            location_states=location_states,
            crew_morale=world_dict.get("crew_morale", 60),
            crew_cohesion=world_dict.get("crew_cohesion", 70),
            panic_level=world_dict.get("panic_level", 25),
            global_flags=world_dict.get("global_flags", {}),
            events_occurred=world_dict.get("events_occurred", []),
            active_threats=world_dict.get("active_threats", [])
        )
    
    @staticmethod
    def game_state_to_snapshot(game_state: GameState) -> Dict[str, Any]:
        """
        Convert GameState Pydantic model back to snapshot format.
        
        This is useful if you want to save a modified GameState back to database.
        
        Args:
            game_state: GameState Pydantic model
            
        Returns:
            Dict: Snapshot format compatible with GameStateManager
        """
        # Convert Pydantic models back to dicts
        state_dict = {
            "game_meta": {
                "game_phase": game_state.phase.value,
                "current_turn_phase": game_state.current_turn_phase.value,
                "current_turn": game_state.turn_count,
                "ending_triggered": game_state.ending_triggered
            },
            "player": game_state.player.model_dump(),
            "npcs": {npc_id: npc.model_dump() for npc_id, npc in game_state.npcs.items()},
            "world": game_state.world.model_dump(exclude={"resources", "ship_systems"}),
            "resources": game_state.world.resources.model_dump(),
            "ship_systems": game_state.world.ship_systems.model_dump(),
            "oracle_sentience_level": game_state.oracle_sentience_level
        }
        
        return {
            "state": state_dict,
            "turn": game_state.turn_count,
            "turn_history": game_state.history
        }


# Usage examples
"""
# In game.py - Converting from database to API response:
from app.utils.state_converter import StateConverter

@router.post("/start")
async def start_game(request, session_mgr):
    session_id = await session_mgr.create_session(request.player_name)
    state_data = await session_mgr.get_state(session_id)
    
    # Convert to GameState model
    game_state = StateConverter.snapshot_to_game_state(state_data, session_id)
    
    return GameStartResponse(
        session_id=session_id,
        opening_narration="...",
        initial_state=game_state,  # Now it's a proper GameState object!
        available_actions=[...],
        oracle_message="..."
    )

# Converting back (if needed):
snapshot = StateConverter.game_state_to_snapshot(game_state)
await session_mgr.update_state(session_id, snapshot)
"""