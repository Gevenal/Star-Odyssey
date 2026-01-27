"""Game data loader - loads and validates all JSON configurations."""

import json
from pathlib import Path
from typing import Dict, List, Optional
from pydantic import ValidationError
from app.game_data.schemas import (
    WorldConfig,
    StateVariablesConfig,
    ActionConfig,
    RandomEventTemplate,
    PersonalityTraitsPool,
    NPCTemplateConfig,
    AIPromptLibrary,
    GameDataBundle,
)


class GameDataLoader:
    """Loads and caches game configuration data."""

    def __init__(self, data_dir: Optional[Path] = None):
        """
        Initialize game data loader.

        Args:
            data_dir: Directory containing JSON config files.
                     Defaults to backend/app/game_data/
        """
        if data_dir is None:
            self.data_dir = Path(__file__).parent
        else:
            self.data_dir = Path(data_dir)

        self._cache: Dict[str, any] = {}

    def _load_json(self, filename: str) -> Dict:
        """
        Load and parse JSON file.

        Args:
            filename: Name of JSON file (e.g., "world_config.json")

        Returns:
            dict: Parsed JSON data

        Raises:
            FileNotFoundError: If file doesn't exist
            json.JSONDecodeError: If JSON is invalid
        """
        file_path = self.data_dir / filename
        if not file_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {file_path}")

        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def load_world_config(self) -> WorldConfig:
        """
        Load world_config.json with validation.

        Returns:
            WorldConfig: Validated world configuration

        Raises:
            ValidationError: If config doesn't match schema
        """
        cache_key = "world_config"
        if cache_key in self._cache:
            return self._cache[cache_key]

        data = self._load_json("world_config.json")
        config = WorldConfig(**data)
        self._cache[cache_key] = config
        return config

    def load_state_variables(self) -> StateVariablesConfig:
        """
        Load state_variables.json with validation.

        Returns:
            StateVariablesConfig: Validated state variables configuration

        Raises:
            ValidationError: If config doesn't match schema
        """
        cache_key = "state_variables"
        if cache_key in self._cache:
            return self._cache[cache_key]

        data = self._load_json("state_variables.json")
        config = StateVariablesConfig(**data)
        self._cache[cache_key] = config
        return config
    
    def get_npc_initial_relationships(self) -> Optional[Dict[str, Dict[str, Any]]]:
        """
        Get initial NPC relationship seeds from state_variables.json.
        
        Returns:
            Dict with initial relationships, or None if not configured
            Format: {"NPC Name": {"Other NPC Name": trust_level, "secret_knowledge": [...], ...}}
        """
        state_vars = self.load_state_variables()
        return state_vars.npc_relationships

    def load_player_actions(self) -> Dict[str, ActionConfig]:
        """
        Load player_actions.json with validation.

        Returns:
            Dict[str, ActionConfig]: Action ID -> ActionConfig mapping

        Raises:
            ValidationError: If config doesn't match schema
        """
        cache_key = "player_actions"
        if cache_key in self._cache:
            return self._cache[cache_key]

        data = self._load_json("player_actions.json")
        actions = {}

        for action_data in data.get("actions", []):
            action = ActionConfig(**action_data)
            actions[action.id] = action

        self._cache[cache_key] = actions
        return actions

    def load_random_events(self) -> List[RandomEventTemplate]:
        """
        Load random_events.json with validation.

        Returns:
            List[RandomEventTemplate]: List of event templates

        Raises:
            ValidationError: If config doesn't match schema
        """
        cache_key = "random_events"
        if cache_key in self._cache:
            return self._cache[cache_key]

        data = self._load_json("random_events.json")
        events = [
            RandomEventTemplate(**event_data)
            for event_data in data.get("events", [])
        ]

        self._cache[cache_key] = events
        return events

    def load_personality_traits(self) -> PersonalityTraitsPool:
        """
        Load personality_traits_pool.json with validation.

        Returns:
            PersonalityTraitsPool: Validated personality traits pool

        Raises:
            ValidationError: If config doesn't match schema
        """
        cache_key = "personality_traits"
        if cache_key in self._cache:
            return self._cache[cache_key]

        data = self._load_json("personality_traits_pool.json")
        pool = PersonalityTraitsPool(**data)
        self._cache[cache_key] = pool
        return pool

    def load_npc_templates(self) -> Dict[str, NPCTemplateConfig]:
        """
        Load npc_templates.json with validation.

        Returns:
            Dict[str, NPCTemplateConfig]: Template ID -> NPCTemplateConfig mapping

        Raises:
            ValidationError: If config doesn't match schema
        """
        cache_key = "npc_templates"
        if cache_key in self._cache:
            return self._cache[cache_key]

        data = self._load_json("npc_templates.json")
        templates = {}

        for template_data in data.get("templates", []):
            template = NPCTemplateConfig(**template_data)
            templates[template.template_id] = template

        self._cache[cache_key] = templates
        return templates

    def load_ai_prompts(self) -> AIPromptLibrary:
        """
        Load ai_prompt_library.json with validation.

        Returns:
            AIPromptLibrary: Validated AI prompt library

        Raises:
            ValidationError: If config doesn't match schema
        """
        cache_key = "ai_prompts"
        if cache_key in self._cache:
            return self._cache[cache_key]

        data = self._load_json("ai_prompt_library.json")
        library = AIPromptLibrary(**data)
        self._cache[cache_key] = library
        return library
    
    def load_oracle_constraints(self) -> Dict[str, Any]:
        """
        Load oracle_constraints.json.

        Returns:
            Dict: Oracle constraints configuration

        Raises:
            FileNotFoundError: If file doesn't exist
        """
        cache_key = "oracle_constraints"
        if cache_key in self._cache:
            return self._cache[cache_key]

        data = self._load_json("oracle_constraints.json")
        self._cache[cache_key] = data
        return data

    def get_all(self) -> GameDataBundle:
        """
        Load all configs and return complete bundle.

        Returns:
            GameDataBundle: Complete validated game data

        Raises:
            ValidationError: If any config doesn't match schema
            FileNotFoundError: If any config file is missing
        """
        return GameDataBundle(
            world_config=self.load_world_config(),
            state_variables=self.load_state_variables(),
            player_actions=self.load_player_actions(),
            random_events=self.load_random_events(),
            personality_traits=self.load_personality_traits(),
            npc_templates=self.load_npc_templates(),
            ai_prompts=self.load_ai_prompts(),
        )

    def clear_cache(self):
        """Clear the configuration cache."""
        self._cache.clear()

    def reload_all(self) -> GameDataBundle:
        """
        Clear cache and reload all configurations.

        Returns:
            GameDataBundle: Freshly loaded game data
        """
        self.clear_cache()
        return self.get_all()

    def get_location(self, location_id: str) -> Optional[Dict]:
        """
        Get location by ID from world config.

        Args:
            location_id: Location identifier

        Returns:
            Optional[dict]: Location data or None
        """
        world_config = self.load_world_config()
        return world_config.locations.get(location_id)

    def get_npc_template(self, template_id: str) -> Optional[NPCTemplateConfig]:
        """
        Get NPC template by ID.

        Args:
            template_id: Template identifier

        Returns:
            Optional[NPCTemplateConfig]: NPC template or None
        """
        templates = self.load_npc_templates()
        return templates.get(template_id)

    def get_action(self, action_id: str) -> Optional[ActionConfig]:
        """
        Get action configuration by ID.

        Args:
            action_id: Action identifier

        Returns:
            Optional[ActionConfig]: Action config or None
        """
        actions = self.load_player_actions()
        return actions.get(action_id)

    def get_event(self, event_id: str) -> Optional[RandomEventTemplate]:
        """
        Get random event template by ID.

        Args:
            event_id: Event identifier

        Returns:
            Optional[RandomEventTemplate]: Event template or None
        """
        events = self.load_random_events()
        for event in events:
            if event.id == event_id:
                return event
        return None


# Global loader instance
_game_data_loader: Optional[GameDataLoader] = None


def get_game_data_loader(data_dir: Optional[Path] = None) -> GameDataLoader:
    """
    Get or create global GameDataLoader instance.

    Args:
        data_dir: Optional data directory override

    Returns:
        GameDataLoader: Global loader instance
    """
    global _game_data_loader
    if _game_data_loader is None:
        _game_data_loader = GameDataLoader(data_dir)
    return _game_data_loader
