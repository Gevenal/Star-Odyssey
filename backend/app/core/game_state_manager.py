"""
Game State Manager - In-Memory Game State Operations
Responsible for reading, writing, and validating game state
"""
import json
import re
from typing import Any, Dict, Optional
from pathlib import Path
from copy import deepcopy


def _default_game_data_dir() -> str:
    """Resolve app/game_data relative to this file (app/core/)."""
    return str((Path(__file__).parent.parent / "game_data").resolve())


class GameStateManager:
    """
    Game State Manager (In-Memory Operations)
    
    Responsibilities:
    1. Load and initialize game state
    2. Provide type-safe state access
    3. Validate state changes
    4. Support snapshot save/load (for persistence)
    
    Not Responsible For:
    - Database persistence (handled by SessionStateManager)
    - Session management
    - Redis caching
    """
    
    from pathlib import Path

    def __init__(self, config_dir: Optional[str] = None, skip_config: bool = False):
        self.turn_history = []

        if skip_config:
            self.config_dir = None
            self.state_config = {}
            self.world_config = {}
            self.state = {}
            return
        
        # app/ 目录
        app_dir = Path(__file__).resolve().parents[1]
        # app/game_data
        default_dir = app_dir / "game_data"
        self.config_dir = Path(config_dir) if config_dir else default_dir

        self.state_config = self._load_json("state_variables.json")
        self.world_config = self._load_json("world_config.json")
        
        # Initialize current state
        self.state = self._initialize_state()
        
        # Turn history (for AI context)
        self.turn_history = []

    def _load_json(self, filename: str) -> Dict:
        """Load JSON configuration file; returns {} if file not found."""
        filepath = self.config_dir / filename
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
    
    def _initialize_state(self) -> Dict:
        """
        Initialize game state from state_variables.json and world_config.json.

        - state_variables: expects "variables": [{"variable_path":"world.resources.X.current","initial_value":...}]
        - world_config: expects top-level "locations": {id: {name, connected_to, default_atmosphere, ...}}
          and "game_settings": {"starting_location": "..."}
        """
        game_settings = self.world_config.get("game_settings", {})
        starting_location = game_settings.get("starting_location", "command_bridge")

        state = {
            "game_meta": {
                "current_turn": 0,
                "current_day": 1,
                "current_hour": 0,
                "game_phase": "intro",
                "started_at": None,
                "last_updated": None,
            },

            # New structure: world contains resources/systems (matches variable_path in state_variables.json)
            "world": {
                "day": 1,
                "turn": 1,
                "time_of_day": "00:00",
                "resources": {},
                "ship_systems": {},
                "location_states": {},
                "crew_morale": 60,
                "crew_cohesion": 70,
                "panic_level": 25,
                "global_flags": {},
                "events_occurred": [],
                "active_threats": []
            },

            "crew_collective": {},
            "mission_progress": {},
            "threats": {},
            "special_events": {},
            "locations": {},
            "npcs": {},

            # Align player structure
            "player": {
                "name": "",
                "health": 100,
                "stress": 0,
                "radiation_exposure": 0,
                "current_location": "command_bridge",
                "inventory": [],
                "reputation": {},
                "discovered_secrets": [],
                "completed_actions": [],
                "flags": {}
            }
        }

        # Read state_variables.json (variables list)
        vars_list = []
        if isinstance(self.state_config, dict):
            vars_list = self.state_config.get("variables", []) or []

        for v in vars_list:
            if not isinstance(v, dict):
                continue
            path = v.get("variable_path")
            if not isinstance(path, str) or not path:
                continue

            init_val = v.get("initial_value", 0)

            # Write to state by variable_path (supports world.resources.xxx.current format)
            self._set_by_path(state, path, init_val)

            # If resource level, also add max/min/critical/decay_rate (for converter/future logic)
            # Only expand for ...current endings
            if path.endswith(".current"):
                base = path[:-len(".current")]
                self._set_by_path(state, f"{base}.max", v.get("max_value", 100.0))
                self._set_by_path(state, f"{base}.min", v.get("min_value", 0.0))
                self._set_by_path(state, f"{base}.critical_threshold", v.get("critical_threshold", 20.0))
                self._set_by_path(state, f"{base}.decay_rate", v.get("decay_rate", 0.0))

        # Location initialization can continue using original code (if in world_config)
        if "world_config" in self.world_config:
            locations = self.world_config["world_config"].get("locations", [])
            for loc in locations:
                loc_id = loc.get("location_id")
                state["locations"][loc_id] = {
                    "name": loc.get("name"),
                    "status": loc.get("current_status", "normal"),
                    "atmosphere": "normal",
                    "accessible": True,
                    "connected_to": loc.get("connected_to", [])
                }

        # Generate NPCs
        try:
            from app.game_data.loader import GameDataLoader
            from app.utils.npc_generator import NPCGenerator
            
            # Load game data
            data_loader = GameDataLoader(data_dir=self.config_dir)
            trait_pool_data = data_loader.load_personality_traits()
            npc_templates = data_loader.load_npc_templates()
            initial_relationships = data_loader.get_npc_initial_relationships()
            
            # Convert traits list to dict grouped by category
            trait_pool_dict = {}
            for trait in trait_pool_data.traits:
                category = trait.category
                if category not in trait_pool_dict:
                    trait_pool_dict[category] = []
                trait_pool_dict[category].append(trait)
            
            # Create NPC generator
            generator = NPCGenerator(
                trait_pool=trait_pool_dict,
                npc_templates=npc_templates
            )
            
            # Get all NPC role IDs (from templates)
            npc_roles = list(npc_templates.keys())
            
            # Generate full crew
            generated_npcs = generator.generate_full_crew(
                roles=npc_roles,
                initial_relationships=initial_relationships
            )
            
            # Convert NPCs to dict format and add to state
            for npc_id, npc in generated_npcs.items():
                # Convert Pydantic model to dict
                npc_dict = npc.model_dump()
                state["npcs"][npc_id] = npc_dict
            
            print(f"[GameStateManager] Generated {len(generated_npcs)} NPCs")
        except Exception as e:
            import traceback
            print(f"[GameStateManager] Warning: Failed to generate NPCs: {e}")
            traceback.print_exc()
            # If NPC generation fails, continue with empty npcs dict

        return state


    def _set_by_path(self, root: Dict[str, Any], path: str, value: Any):
        keys = path.split(".")
        cur = root
        for k in keys[:-1]:
            if k not in cur or not isinstance(cur[k], dict):
                cur[k] = {}
            cur = cur[k]
        cur[keys[-1]] = value

    # ===== State Access Methods =====
    
    def get(self, path: str, default: Any = None) -> Any:
        """
        Get state value (supports path notation)
        
        Examples:
        >>> state.get("resources.oxygen_level")
        100
        >>> state.get("npcs.captain.health")
        100
        >>> state.get("nonexistent.path", default=0)
        0
        
        Args:
            path: Dot-separated path, e.g. "resources.oxygen_level"
            default: Default value if path doesn't exist
            
        Returns:
            State value or default value
        """
        keys = path.split(".")
        value = self.state
        
        try:
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, path: str, value: Any, validate: bool = True) -> bool:
        """
        Set state value
        
        Args:
            path: Dot-separated path
            value: Value to set
            validate: Whether to validate the value
            
        Returns:
            Whether the operation was successful
        """
        if validate and not self._validate_value(path, value):
            print(f"[StateManager] Rejected setting {path} = {value}: validation failed")
            return False
        
        keys = path.split(".")
        target = self.state
        
        # Navigate to target location
        for key in keys[:-1]:
            if key not in target:
                target[key] = {}
            target = target[key]
        
        # Set value
        old_value = target.get(keys[-1])
        target[keys[-1]] = value
        
        # Log change (for debugging)
        if old_value != value:
            print(f"[StateManager] {path}: {old_value} → {value}")
        
        return True
    
    def modify(self, path: str, delta: float, validate: bool = True) -> bool:
        """
        Modify numeric value incrementally
        
        Example:
        >>> state.modify("resources.oxygen_level", -2.5)
        True
        
        Args:
            path: State path
            delta: Change amount (positive to increase, negative to decrease)
            validate: Whether to validate result value
            
        Returns:
            Whether modification was successful
        """
        current = self.get(path, 0)
        
        if not isinstance(current, (int, float)):
            print(f"[StateManager] Cannot modify non-numeric type: {path} = {current}")
            return False
        
        new_value = current + delta
        return self.set(path, new_value, validate=validate)
    
    def _validate_value(self, path: str, value: Any) -> bool:
        """
        Validate if value is legal
        
        Checks:
        1. Whether numeric value is within min/max range
        2. Whether enum value is in allowed list
        """
        # Find constraints from state_config
        # Simplified version: only check resource and system ranges
        
        parts = path.split(".")
        if len(parts) >= 2:
            category = parts[0]  # resources, ship_systems, etc.
            key = parts[1]
            
            if "state_variables" in self.state_config:
                category_config = self.state_config["state_variables"].get(category, {})
                if key in category_config:
                    config = category_config[key]
                    
                    # Check numeric range
                    if isinstance(value, (int, float)):
                        min_val = config.get("min_value")
                        max_val = config.get("max_value")
                        
                        if min_val is not None and value < min_val:
                            print(f"[Validation] {path}={value} below minimum {min_val}")
                            return False
                        
                        if max_val is not None and value > max_val:
                            print(f"[Validation] {path}={value} above maximum {max_val}")
                            return False
        
        return True

    def to_game_state_model(self, session_id: str) -> "GameState":
        """
        Convert internal state to GameState Pydantic model.
        
        Args:
            session_id: Session identifier
            
        Returns:
            GameState: Pydantic model instance
        """
        from app.models.game_state import GameState
        from app.models.player import PlayerState
        from app.models.world import WorldState
        from app.models.npc import NPCState
        from app.models.enums import GamePhase
        
        # Extract data from internal state
        player_data = self.state.get("player", {})
        npcs_data = self.state.get("npcs", {})
        world_data = self.state.get("world", {})
        game_meta = self.state.get("game_meta", {})
        
        # Convert to Pydantic models
        player = PlayerState(
            name=player_data.get("name", "Unknown"),
            health=player_data.get("health", 100),
            stress=player_data.get("stress", 0),
            location=player_data.get("location", "cryosleep_bay"),
            inventory=player_data.get("inventory", [])
        )
        
        # Convert NPCs
        npcs = {}
        for npc_id, npc_data in npcs_data.items():
            npcs[npc_id] = NPCState(**npc_data)
        
        # Convert world state
        world = WorldState(
            day=world_data.get("day", 1),
            time_of_day=world_data.get("time_of_day", "morning"),
            global_flags=world_data.get("global_flags", {}),
            events_occurred=world_data.get("events_occurred", [])
        )
        
        # Create GameState
        return GameState(
            session_id=session_id,
            phase=GamePhase(game_meta.get("game_phase", "intro")),
            player=player,
            npcs=npcs,
            world=world,
            turn_count=game_meta.get("current_turn", 0),
            history=self.turn_history
        )
        
    # ===== Batch Operations =====
    
    def apply_delta(self, delta: Dict[str, Any]) -> bool:
        """
        Apply state changes (typically from AI output)
        
        Args:
            delta: State change dictionary, format:
                {
                    "resources.oxygen_level": -5,
                    "crew_collective.panic_level": 10,
                    "npcs.captain.stress": 5
                }
                
        Returns:
            Whether all changes were successfully applied
        """
        success = True
        
        for path, change in delta.items():
            # Determine if incremental or absolute
            if isinstance(change, str) and (change.startswith('+') or change.startswith('-')):
                # Incremental: "+10" or "-5"
                delta_value = float(change)
                if not self.modify(path, delta_value):
                    success = False
            else:
                # Absolute value
                if not self.set(path, change):
                    success = False
        
        return success
    
    # ===== Snapshot Management =====
    
    def get_snapshot(self) -> Dict:
        """
        Get complete state snapshot (deep copy)
        
        Used for:
        1. Saving game
        2. Passing to AI as context
        3. Turn history recording
        """
        return {
            "state": deepcopy(self.state),
            "turn": self.get("game_meta.current_turn"),
            "turn_history": self.turn_history[-5:] if self.turn_history else []  # Last 5 turns
        }
    
    def load_snapshot(self, snapshot: Dict):
        """
        Restore state from snapshot
        
        Args:
            snapshot: Snapshot previously obtained via get_snapshot()
        """
        if "state" in snapshot:
            self.state = deepcopy(snapshot["state"])
        
        if "turn_history" in snapshot:
            self.turn_history = snapshot["turn_history"]
    
    # ===== Persistence (Simplified Version) =====
    
    def save_to_file(self, filepath: str = "savegame.json"):
        """
        Save state to JSON file
        
        Args:
            filepath: Save path
        """
        snapshot = self.get_snapshot()
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(snapshot, f, indent=2, ensure_ascii=False)
        
        print(f"[StateManager] State saved to {filepath}")
    
    def load_from_file(self, filepath: str = "savegame.json"):
        """
        Load state from JSON file
        
        Args:
            filepath: File path
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                snapshot = json.load(f)
            
            self.load_snapshot(snapshot)
            print(f"[StateManager] State loaded from {filepath}")
            return True
        except FileNotFoundError:
            print(f"[StateManager] File not found: {filepath}")
            return False
    
    # ===== Helper Methods =====
    
    def get_recent_turns(self, n: int = 3) -> list:
        """Get last N turns from history"""
        return self.turn_history[-n:] if len(self.turn_history) >= n else self.turn_history
    
    def add_turn_to_history(self, turn_data: Dict):
        """Add turn record to history"""
        self.turn_history.append(turn_data)
        
        # Limit history length (avoid memory explosion)
        if len(self.turn_history) > 50:
            self.turn_history = self.turn_history[-50:]
    
    def increment_turn(self):
        """Increment turn counter"""
        self.modify("game_meta.current_turn", 1, validate=False)
        
        # Calculate in-game time
        current_turn = self.get("game_meta.current_turn")
        hours = current_turn * 2  # 2 hours per turn
        day = (hours // 24) + 1
        hour = hours % 24
        turn_in_day = (hour // 2) + 1
        max_days = 3
        if day > max_days:
            day = max_days
        
        self.set("game_meta.current_day", day, validate=False)
        self.set("game_meta.current_hour", hour, validate=False)
        self.set("world.day", day, validate=False)
        self.set("world.time_of_day", f"{hour:02d}:00", validate=False)
        # Keep world.turn within 1-12 for the current day
        self.set("world.turn", turn_in_day, validate=False)

# ===== Usage Example =====
if __name__ == "__main__":
    # Initialize
    state = GameStateManager()
    
    # Read state
    print(f"Initial oxygen: {state.get('resources.oxygen_level')}%")
    print(f"Reactor integrity: {state.get('ship_systems.reactor_integrity')}%")
    
    # Modify state
    state.modify("resources.oxygen_level", -2.5)
    print(f"After degradation: {state.get('resources.oxygen_level')}%")
    
    # Apply AI output changes
    ai_delta = {
        "resources.oxygen_level": -5,
        "crew_collective.panic_level": 10,
        "ship_systems.hull_integrity": -3
    }
    state.apply_delta(ai_delta)
    
    # Save state
    state.save_to_file("test_save.json")
    
    # Increment turn
    state.increment_turn()
    print(f"Current turn: {state.get('game_meta.current_turn')}")
    print(f"Day {state.get('game_meta.current_day')}, Hour {state.get('game_meta.current_hour')}")
    
    print("\n✅ GameStateManager test complete!")

