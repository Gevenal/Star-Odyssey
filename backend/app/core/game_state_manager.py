"""
Game State Manager - In-Memory Game State Operations
Responsible for reading, writing, and validating game state
"""
import json
from typing import Any, Dict, Optional
from pathlib import Path
from copy import deepcopy


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

    def __init__(self, config_dir: Optional[str] = None):
        # app/ 目录
        app_dir = Path(__file__).resolve().parents[1]
        # app/game_data
        default_dir = app_dir / "game_data"
        self.config_dir = Path(config_dir) if config_dir else default_dir

        self.state_config = self._load_json("state_variables.json")
        self.world_config = self._load_json("world_config.json")
        self.state = self._initialize_state()
        self.turn_history = []
    
    def _load_json(self, filename: str) -> Dict:
        """Load JSON configuration file"""
        filepath = self.config_dir / filename
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _initialize_state(self) -> Dict:
        """
        Initialize game state from configuration files
        
        Based on state_variables.json and world_config.json
        """
        state = {
            # Metadata
            "game_meta": {
                "current_turn": 0,
                "current_day": 1,
                "current_hour": 0,  # In-game time (0-168 hours, 7 days)
                "game_phase": "intro",  # intro, playing, crisis, ending
                "started_at": None,
                "last_updated": None
            },
            
            # Resources (read initial values from state_variables.json)
            "resources": {},
            
            # Ship systems
            "ship_systems": {},
            
            # Crew collective state
            "crew_collective": {},
            
            # Mission progress
            "mission_progress": {},
            
            # Environmental threats
            "threats": {},
            
            # Special event flags
            "special_events": {},
            
            # Location states (read from world_config.json)
            "locations": {},
            
            # NPC states (filled later by NPC generator)
            "npcs": {},
            
            # Player state
            "player": {
                "name": "",
                "health": 100,
                "stress": 0,
                "current_location": "command_bridge",
                "inventory": [],
                "known_secrets": [],
                "completed_actions": []
            }
        }
        
        # Fill resource initial values
        if "state_variables" in self.state_config:
            resources_config = self.state_config["state_variables"].get("resources", {})
            for key, config in resources_config.items():
                state["resources"][key] = config.get("current_value", 0)
            
            # Fill ship systems
            systems_config = self.state_config["state_variables"].get("ship_systems", {})
            for key, config in systems_config.items():
                state["ship_systems"][key] = config.get("current_value", 0)
            
            # Fill crew state
            crew_config = self.state_config["state_variables"].get("crew_collective", {})
            for key, config in crew_config.items():
                state["crew_collective"][key] = config.get("current_value", 50)
            
            # Fill mission progress
            mission_config = self.state_config["state_variables"].get("mission_progress", {})
            for key, config in mission_config.items():
                state["mission_progress"][key] = config.get("current_value", False)
        
        # Fill location states
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
        
        return state
    
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
        
        self.set("game_meta.current_day", day, validate=False)
        self.set("game_meta.current_hour", hour, validate=False)


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

