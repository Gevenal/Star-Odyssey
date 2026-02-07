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

    @staticmethod
    def _non_empty_str(x, default="Unknown"):
        if isinstance(x, str) and x.strip():
            return x.strip()
        return default

    @staticmethod
    def snapshot_to_game_state(snapshot: Dict[str, Any], session_id: str) -> GameState:
        # Snapshot may be {"state": {...}, "turn":..., "turn_history":...}
        # Or {"state": {"state": {...}}, "turn":..., "turn_history":...}
        state_dict = snapshot.get("state", {}) if isinstance(snapshot, dict) else {}

        # Compatible with old structure: extra layer of state
        if isinstance(state_dict, dict) and isinstance(state_dict.get("state"), dict):
            inner = state_dict["state"]
            if any(k in inner for k in ("game_meta", "player", "world", "resources", "ship_systems", "npcs")):
                state_dict = inner

        # Player: compatible with multiple paths
        player_dict = state_dict.get("player", {})
        if not player_dict and isinstance(state_dict.get("state"), dict):
            # Fallback for extreme cases
            player_dict = state_dict["state"].get("player", {})

        player = StateConverter._convert_player(player_dict)

        # NPCs
        npcs = StateConverter._convert_npcs(state_dict.get("npcs", {}))

        # World/resources/systems: compatible with world.resources structure
        world_dict = state_dict.get("world", {}) if isinstance(state_dict, dict) else {}

        resources_dict = state_dict.get("resources", {})
        if (not resources_dict) and isinstance(world_dict, dict):
            resources_dict = world_dict.get("resources", {})

        systems_dict = state_dict.get("ship_systems", {})
        if (not systems_dict) and isinstance(world_dict, dict):
            systems_dict = world_dict.get("ship_systems", {})

        world = StateConverter._convert_world(world_dict, resources_dict, systems_dict)

        game_meta = state_dict.get("game_meta", {}) if isinstance(state_dict, dict) else {}

        return GameState(
            session_id=session_id,
            phase=GamePhase(game_meta.get("game_phase", "intro")),
            current_turn_phase=TurnPhase(game_meta.get("current_turn_phase", "player_turn")),
            player=player,
            npcs=npcs,
            world=world,
            turn_count=max(1, game_meta.get("current_turn", 0)),
            history=snapshot.get("turn_history", []) if isinstance(snapshot, dict) else [],
            oracle_sentience_level=state_dict.get("oracle_sentience_level", 1) if isinstance(state_dict, dict) else 1,
            ending_triggered=game_meta.get("ending_triggered")
        )

    @staticmethod
    def _convert_player(player_dict: Dict[str, Any]) -> PlayerState:
        return PlayerState(
            name=StateConverter._non_empty_str(player_dict.get("name"), "Unknown"),
            health=player_dict.get("health", 100),
            stress=player_dict.get("stress", 0),
            radiation_exposure=player_dict.get("radiation_exposure", 0.0),
            location=player_dict.get("location", player_dict.get("current_location", "cryo_bay")),
            inventory=player_dict.get("inventory", []),
            reputation=player_dict.get("reputation", {}),
            discovered_secrets=player_dict.get("discovered_secrets", player_dict.get("known_secrets", [])),
            completed_actions=player_dict.get("completed_actions", []),
            flags=player_dict.get("flags", {}),
            active_quests=player_dict.get("active_quests", []),
            completed_quests=player_dict.get("completed_quests", [])
        )
    
    @staticmethod
    def _convert_npcs(npcs_dict: Dict[str, Any]) -> Dict[str, NPCState]:
        # Simple fallback: return empty if no NPCs
        if not isinstance(npcs_dict, dict):
            return {}
        npcs: Dict[str, NPCState] = {}
        for npc_id, npc_data in npcs_dict.items():
            try:
                # If npc_data is already a dict (from model_dump()), convert directly
                if isinstance(npc_data, dict):
                    # Ensure personality field is PersonalityTraits object
                    if "personality" in npc_data and isinstance(npc_data["personality"], dict):
                        npc_data["personality"] = PersonalityTraits(**npc_data["personality"])
                    
                    # Ensure each relationship in relationships is NPCRelationship object
                    if "relationships" in npc_data and isinstance(npc_data["relationships"], dict):
                        relationships = {}
                        for rel_key, rel_data in npc_data["relationships"].items():
                            if isinstance(rel_data, dict):
                                relationships[rel_key] = NPCRelationship(**rel_data)
                            else:
                                relationships[rel_key] = rel_data
                        npc_data["relationships"] = relationships
                    
                    # Ensure secrets is a list of NPCSecret objects
                    if "secrets" in npc_data and isinstance(npc_data["secrets"], list):
                        secrets = []
                        for secret_data in npc_data["secrets"]:
                            if isinstance(secret_data, dict):
                                secrets.append(NPCSecret(**secret_data))
                            else:
                                secrets.append(secret_data)
                        npc_data["secrets"] = secrets
                    
                    # Ensure skills field exists (set to empty dict if missing)
                    if "skills" not in npc_data:
                        npc_data["skills"] = {}
                    
                    # Ensure inventory field exists (set to empty list if missing)
                    if "inventory" not in npc_data:
                        npc_data["inventory"] = []
                    
                    # Create NPCState object
                    npcs[npc_id] = NPCState(**npc_data)
                elif isinstance(npc_data, NPCState):
                    # If already NPCState object, use directly
                    npcs[npc_id] = npc_data
            except Exception as e:
                print(f"[StateConverter] Warning: Failed to convert NPC {npc_id}: {e}")
                continue
        return npcs

    @staticmethod
    def _convert_world(
        world_dict: Dict[str, Any],
        resources_dict: Dict[str, Any],
        systems_dict: Dict[str, Any]
    ) -> WorldState:
        """
        PLACEHOLDER: Convert world/resources/systems dicts to WorldState.
        Returns a minimal valid WorldState with safe defaults.
        """

        # ---- helpers ----
        def make_resource_level(res_data) -> ResourceLevel:
            def clamp(v: float, lo: float, hi: float) -> float:
                return max(lo, min(hi, v))

            if isinstance(res_data, dict):
                mx = float(res_data.get("max", 100.0))
                mn = float(res_data.get("min", 0.0))
                cur = float(res_data.get("current", mx))
                cur = clamp(cur, mn, mx)
                return ResourceLevel(
                    current=cur,
                    max=mx,
                    min=mn,
                    critical_threshold=float(res_data.get("critical_threshold", 20.0)),
                    decay_rate=float(res_data.get("decay_rate", 0.0)),
                )

            if isinstance(res_data, (int, float)):
                cur = float(res_data)
                cur = clamp(cur, 0.0, 100.0)
                return ResourceLevel(current=cur, max=100.0, min=0.0, critical_threshold=20.0, decay_rate=0.0)

            return ResourceLevel(current=100.0, max=100.0, min=0.0, critical_threshold=20.0, decay_rate=0.0)

        def make_system_integrity(sys_data) -> SystemIntegrity:
            if isinstance(sys_data, dict):
                integrity = float(sys_data.get("integrity", 100.0))
                return SystemIntegrity(
                    integrity=integrity,
                    operational=bool(sys_data.get("operational", integrity > 25.0)),
                    degradation_rate=float(sys_data.get("degradation_rate", 0.5)),
                )
            if isinstance(sys_data, (int, float)):
                integrity = float(sys_data)
                return SystemIntegrity(integrity=integrity, operational=integrity > 25.0, degradation_rate=0.5)
            return SystemIntegrity(integrity=100.0, operational=True, degradation_rate=0.5)

        # ---- resources ----
        resources = ResourceLevels(
            oxygen_level=make_resource_level(resources_dict.get("oxygen_level", 85.0)),
            fuel_reserves=make_resource_level(resources_dict.get("fuel_reserves", 60.0)),
            power_level=make_resource_level(resources_dict.get("power_level", 75.0)),
            medical_supplies=make_resource_level(resources_dict.get("medical_supplies", 50.0)),
            food_water=make_resource_level(resources_dict.get("food_water", resources_dict.get("food_supply", 70.0))),
            repair_materials=make_resource_level(resources_dict.get("repair_materials", resources_dict.get("spare_parts", 40.0))),
        )

        # ---- ship systems ----
        ship_systems = ShipSystems(
            reactor_integrity=make_system_integrity(systems_dict.get("reactor_integrity", 80.0)),
            hull_integrity=make_system_integrity(systems_dict.get("hull_integrity", 65.0)),
            life_support_efficiency=make_system_integrity(systems_dict.get("life_support_efficiency", 75.0)),
            navigation_systems=make_system_integrity(systems_dict.get("navigation_systems", 55.0)),
            communications_array=make_system_integrity(systems_dict.get("communications_array", 30.0)),
            escape_pods_ready=systems_dict.get("escape_pods_ready", 6),
        )

        # ---- location states (placeholder empty) ----
        location_states: Dict[str, LocationState] = {}

        # ---- time/turn ----
        day = int(world_dict.get("day", 1)) if isinstance(world_dict, dict) else 1
        time_of_day = world_dict.get("time_of_day", "00:00") if isinstance(world_dict, dict) else "00:00"
        turn = int(world_dict.get("turn", 1)) if isinstance(world_dict, dict) else 1
        day = max(1, min(3, day))
        turn = max(1, min(12, turn))

        return WorldState(
            day=day,
            turn=turn,
            time_of_day=time_of_day,
            resources=resources,
            ship_systems=ship_systems,
            location_states=location_states,
            crew_morale=int(world_dict.get("crew_morale", 60)) if isinstance(world_dict, dict) else 60,
            crew_cohesion=int(world_dict.get("crew_cohesion", 70)) if isinstance(world_dict, dict) else 70,
            panic_level=int(world_dict.get("panic_level", 25)) if isinstance(world_dict, dict) else 25,
            global_flags=world_dict.get("global_flags", {}) if isinstance(world_dict, dict) else {},
            events_occurred=world_dict.get("events_occurred", []) if isinstance(world_dict, dict) else [],
            active_threats=world_dict.get("active_threats", []) if isinstance(world_dict, dict) else [],
        )


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