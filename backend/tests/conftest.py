"""Pytest configuration and fixtures."""
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime

from app.models.game_state import GameState, PlayerState, WorldState
from app.models.npc import NPCState, PersonalityTraits, NPCRelationship
from app.models.action import PlayerAction
from app.models.resources import ResourceLevel, ResourceLevels
from app.models.enums import GamePhase, TurnPhase, Atmosphere


@pytest_asyncio.fixture
async def mock_gemini_client():
    """Mock Gemini client for testing."""
    client = AsyncMock()
    client.generate_text.return_value = "Test narration response"
    client.generate_json.return_value = {
        "narration": "Test narration",
        "state_changes": [],
        "npc_reactions": []
    }
    return client


@pytest.fixture
def sample_resource_level():
    """Sample resource level for testing."""
    return ResourceLevel(
        current=50,
        max=100,
        min=0,
        critical_threshold=20,
        decay_rate=2.0
    )


@pytest.fixture
def sample_resource_levels(sample_resource_level):
    """Sample resource levels for testing."""
    return ResourceLevels(
        oxygen_level=sample_resource_level.model_copy(),
        fuel_reserves=sample_resource_level.model_copy(),
        power_level=sample_resource_level.model_copy(),
        medical_supplies=sample_resource_level.model_copy(),
        food_water=sample_resource_level.model_copy(),
        repair_materials=sample_resource_level.model_copy()
    )


@pytest.fixture
def sample_personality():
    """Sample NPC personality for testing."""
    return PersonalityTraits(
        core_value="loyalty",
        social_style="leader",
        stress_response="takes_charge",
        decision_making="data_driven",
        morality="pragmatic_moral",
        quirks=["perfectionist", "coffee_addict"]
    )


@pytest.fixture
def sample_npc(sample_personality):
    """Sample NPC for testing."""
    return NPCState(
        id="test_npc_001",
        name="Dr. Sarah Chen",
        role="Medical Officer",
        location="Medical Bay",
        alive=True,
        health=100,
        stress_level=30,
        personality=sample_personality,
        relationships={},
        goals=["Keep crew healthy", "Research radiation effects"],
        current_activity="Checking medical supplies"
    )


@pytest.fixture
def sample_player_state():
    """Sample player state for testing."""
    return PlayerState(
        name="Commander",
        health=100,
        stress=25,
        radiation_exposure=0,
        location="Bridge",
        inventory=["access_card", "repair_kit"],
        reputation={"Dr. Chen": 75, "Engineer Torres": 60},
        discovered_secrets=["crew_manifest_anomaly"],
        flags={"reactor_inspected": True}
    )


@pytest.fixture
def sample_world_state(sample_resource_levels):
    """Sample world state for testing."""
    return WorldState(
        day=3,
        turn=15,
        time_of_day="Morning",
        resources=sample_resource_levels,
        crew_morale=65,
        crew_cohesion=70,
        panic_level=25,
        global_flags={"emergency_protocol_active": True},
        events_occurred=["micrometeorite_storm", "power_fluctuation"],
        active_threats=["radiation_leak"]
    )


@pytest.fixture
def sample_game_state(sample_player_state, sample_world_state, sample_npc):
    """Sample game state for testing."""
    return GameState(
        session_id="test_session_123",
        phase=GamePhase.PLAYING,
        current_turn_phase=TurnPhase.PLAYER_TURN,
        player=sample_player_state,
        npcs={"test_npc_001": sample_npc},
        world=sample_world_state,
        turn_count=15,
        oracle_sentience_level=35
    )


@pytest.fixture
def sample_player_action():
    """Sample player action for testing."""
    return PlayerAction(
        session_id="test_session_123",
        action_type="freeform",
        action_id="custom_action",
        action_text="I check the reactor controls for damage",
        target_location="Reactor Room",
        target_npc=None,
        target_item=None
    )


@pytest_asyncio.fixture
async def test_database():
    """In-memory test database."""
    # TODO: Setup test MongoDB (mongomock or similar)
    # For now, return a mock
    return MagicMock()


@pytest.fixture
def mock_game_data_loader():
    """Mock game data loader."""
    loader = MagicMock()
    loader.load_npc_templates.return_value = {}
    loader.load_personality_traits.return_value = {}
    loader.load_world_config.return_value = MagicMock()
    return loader


@pytest.fixture
def mock_redis_cache():
    """Mock Redis cache."""
    cache = AsyncMock()
    cache.get_game_state.return_value = None
    cache.set_game_state.return_value = None
    return cache
