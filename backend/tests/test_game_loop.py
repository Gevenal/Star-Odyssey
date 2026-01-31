"""Tests for game loop."""
import pytest
from unittest.mock import AsyncMock, MagicMock
from app.core.game_loop import GameLoop
from app.core.rules.engine import RulesEngine
from app.core.rules.base_rule import RuleResult
from app.ai.schemas.game_response import (
    GameActionResponse as AIGameActionResponse,
    Mood as AIMood,
    ConfidenceLevel as AIConfidenceLevel,
)


def _minimal_snapshot():
    """Minimal snapshot for GameStateManager.load_snapshot and StateConverter."""
    return {
        "state": {
            "game_meta": {"game_phase": "playing", "current_turn": 1, "current_day": 1, "current_hour": 0},
            "player": {
                "name": "Test",
                "health": 100,
                "stress": 0,
                "location": "bridge",
                "inventory": [],
                "reputation": {},
                "discovered_secrets": [],
                "completed_actions": [],
                "flags": {},
            },
            "resources": {"oxygen_level": 85.0},
            "ship_systems": {},
            "crew_collective": {},
            "npcs": {},
            "locations": {},
        },
        "turn": 1,
        "turn_history": [],
    }


@pytest.fixture
def mock_state_manager():
    m = AsyncMock()
    m.get_state = AsyncMock(return_value=_minimal_snapshot())
    m.update_state = AsyncMock(return_value=True)
    return m


@pytest.fixture
def mock_gemini_for_loop():
    m = AsyncMock()
    m.generate_structured = AsyncMock(
        return_value=AIGameActionResponse(
            success=True,
            narration="You check the reactor. The readings are stable.",
            mood=AIMood.TENSE,
            confidence_level=AIConfidenceLevel.HIGH,
            state_changes=[],
            resource_changes=[],
            npc_reactions=[],
            available_actions=["check_systems", "talk_to_oracle"],
            trigger_ending=False,
            ending_id=None,
        )
    )
    return m


@pytest.fixture
def mock_rules_engine():
    m = AsyncMock()
    m.validate_action = AsyncMock(return_value=RuleResult(valid=True))
    return m


class TestGameLoop:
    """Test suite for main game loop."""

    @pytest.mark.asyncio
    async def test_process_action_returns_response(
        self, sample_player_action, mock_state_manager, mock_gemini_for_loop, mock_rules_engine
    ):
        """process_action: with mocked deps, returns GameActionResponse with narration and state persisted."""
        loop = GameLoop(
            state_manager=mock_state_manager,
            rules_engine=mock_rules_engine,
            gemini_client=mock_gemini_for_loop,
        )
        resp = await loop.process_action("sess-1", sample_player_action)
        assert resp.success is True
        assert resp.narration
        assert "reactor" in resp.narration.lower() or "readings" in resp.narration.lower()
        assert resp.trigger_ending is False
        mock_state_manager.get_state.assert_called_once_with("sess-1")
        mock_state_manager.update_state.assert_called_once()
        mock_rules_engine.validate_action.assert_called_once()
        mock_gemini_for_loop.generate_structured.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_action_invalid_raises(
        self, sample_player_action, mock_state_manager, mock_gemini_for_loop, mock_rules_engine
    ):
        """When rules_engine returns valid=False, process_action raises ValueError (API will 400)."""
        mock_rules_engine.validate_action = AsyncMock(
            return_value=RuleResult(valid=False, error="Insufficient oxygen")
        )
        loop = GameLoop(
            state_manager=mock_state_manager,
            rules_engine=mock_rules_engine,
            gemini_client=mock_gemini_for_loop,
        )
        with pytest.raises(ValueError) as exc:
            await loop.process_action("sess-1", sample_player_action)
        assert "Insufficient oxygen" in str(exc.value)
        mock_gemini_for_loop.generate_structured.assert_not_called()
        mock_state_manager.update_state.assert_not_called()


class TestGameLoopE2E:
    """End-to-end tests with real RulesEngine and GameDataLoader."""

    @pytest.fixture
    def real_rules_engine(self):
        """Real RulesEngine with GameDataLoader."""
        from app.core.rules.engine import RulesEngine
        from app.game_data.loader import get_game_data_loader
        return RulesEngine(game_data_loader=get_game_data_loader())

    @pytest.fixture
    def snapshot_at_command_bridge(self):
        """Snapshot with player at command_bridge (required for check_systems)."""
        return {
            "state": {
                "game_meta": {"game_phase": "playing", "current_turn": 1, "current_day": 1, "current_hour": 0},
                "player": {
                    "name": "TestPlayer",
                    "health": 100,
                    "stress": 20,
                    "location": "command_bridge",  # Required for check_systems
                    "inventory": [],
                    "reputation": {},
                    "discovered_secrets": [],
                    "completed_actions": [],
                    "flags": {},
                },
                "resources": {
                    "oxygen_level": {"current": 85.0, "max": 100.0, "min": 0.0, "critical_threshold": 25.0},
                    "fuel_reserves": {"current": 60.0, "max": 100.0, "min": 0.0, "critical_threshold": 15.0},
                    "power_level": {"current": 75.0, "max": 100.0, "min": 0.0, "critical_threshold": 20.0},
                },
                "ship_systems": {},
                "crew_collective": {},
                "npcs": {},
                "locations": {},
            },
            "turn": 1,
            "turn_history": [],
        }

    @pytest.fixture
    def mock_state_manager_e2e(self, snapshot_at_command_bridge):
        """State manager that returns snapshot_at_command_bridge."""
        m = AsyncMock()
        m.get_state = AsyncMock(return_value=snapshot_at_command_bridge)
        m.update_state = AsyncMock(return_value=True)
        return m

    @pytest.mark.asyncio
    async def test_e2e_check_systems_success(
        self, real_rules_engine, mock_state_manager_e2e, mock_gemini_for_loop, snapshot_at_command_bridge
    ):
        """
        E2E: Player at command_bridge executes check_systems.
        - RulesEngine validates location requirement ✓
        - AI generates response
        - State is updated and saved
        """
        from app.models.action import PlayerAction
        from app.models.enums import ActionCategory

        action = PlayerAction(
            session_id="e2e-sess-1",
            action_type=ActionCategory.INVESTIGATION,
            action_id="check_systems",
            action_text="I check the ship systems",
        )

        loop = GameLoop(
            state_manager=mock_state_manager_e2e,
            rules_engine=real_rules_engine,
            gemini_client=mock_gemini_for_loop,
        )

        resp = await loop.process_action("e2e-sess-1", action)

        # Assertions
        assert resp.success is True
        assert resp.narration
        assert resp.trigger_ending is False

        # Verify rules were checked (real validation passed)
        mock_state_manager_e2e.get_state.assert_called_once()
        mock_state_manager_e2e.update_state.assert_called_once()
        mock_gemini_for_loop.generate_structured.assert_called_once()

    @pytest.mark.asyncio
    async def test_e2e_check_systems_wrong_location(
        self, real_rules_engine, mock_state_manager_e2e, mock_gemini_for_loop
    ):
        """
        E2E: Player at cryo_bay tries check_systems (requires command_bridge).
        - ResourceAvailabilityRule should reject (location mismatch)
        - No AI call, no state update
        """
        from app.models.action import PlayerAction
        from app.models.enums import ActionCategory

        # Modify snapshot: player at wrong location
        wrong_snapshot = {
            "state": {
                "game_meta": {"game_phase": "playing", "current_turn": 1, "current_day": 1, "current_hour": 0},
                "player": {
                    "name": "TestPlayer",
                    "health": 100,
                    "stress": 20,
                    "location": "cryo_bay",  # Wrong location for check_systems
                    "inventory": [],
                    "reputation": {},
                    "discovered_secrets": [],
                    "completed_actions": [],
                    "flags": {},
                },
                "resources": {
                    "oxygen_level": {"current": 85.0, "max": 100.0, "min": 0.0, "critical_threshold": 25.0},
                },
                "ship_systems": {},
                "crew_collective": {},
                "npcs": {},
                "locations": {},
            },
            "turn": 1,
            "turn_history": [],
        }
        mock_state_manager_e2e.get_state = AsyncMock(return_value=wrong_snapshot)

        action = PlayerAction(
            session_id="e2e-sess-2",
            action_type=ActionCategory.INVESTIGATION,
            action_id="check_systems",
            action_text="I check the ship systems",
        )

        loop = GameLoop(
            state_manager=mock_state_manager_e2e,
            rules_engine=real_rules_engine,
            gemini_client=mock_gemini_for_loop,
        )

        with pytest.raises(ValueError) as exc:
            await loop.process_action("e2e-sess-2", action)

        # Should mention location requirement
        assert "command_bridge" in str(exc.value).lower() or "location" in str(exc.value).lower()

        # No AI call, no state update
        mock_gemini_for_loop.generate_structured.assert_not_called()
        mock_state_manager_e2e.update_state.assert_not_called()

    @pytest.mark.asyncio
    async def test_e2e_location_topology_invalid_movement(
        self, real_rules_engine, mock_state_manager_e2e, mock_gemini_for_loop
    ):
        """
        E2E: Player tries to move from cryo_bay to engineering (not connected).
        - LocationTopologyRule should reject
        - No AI call, no state update
        """
        from app.models.action import PlayerAction
        from app.models.enums import ActionCategory

        # cryo_bay is connected to ["crew_quarters", "med_bay"], not engineering
        snapshot = {
            "state": {
                "game_meta": {"game_phase": "playing", "current_turn": 1, "current_day": 1, "current_hour": 0},
                "player": {
                    "name": "TestPlayer",
                    "health": 100,
                    "stress": 20,
                    "location": "cryo_bay",
                    "inventory": [],
                    "reputation": {},
                    "discovered_secrets": [],
                    "completed_actions": [],
                    "flags": {},
                },
                "resources": {
                    "oxygen_level": {"current": 85.0, "max": 100.0, "min": 0.0, "critical_threshold": 25.0},
                },
                "ship_systems": {},
                "crew_collective": {},
                "npcs": {},
                "locations": {},
            },
            "turn": 1,
            "turn_history": [],
        }
        mock_state_manager_e2e.get_state = AsyncMock(return_value=snapshot)

        action = PlayerAction(
            session_id="e2e-sess-3",
            action_type=ActionCategory.INVESTIGATION,
            action_id="explore_location",
            action_text="I move to engineering",
            target_location="engineering",  # Not connected from cryo_bay
        )

        loop = GameLoop(
            state_manager=mock_state_manager_e2e,
            rules_engine=real_rules_engine,
            gemini_client=mock_gemini_for_loop,
        )

        with pytest.raises(ValueError) as exc:
            await loop.process_action("e2e-sess-3", action)

        # Should mention cannot reach or connected locations
        error_msg = str(exc.value).lower()
        assert "engineering" in error_msg or "cannot reach" in error_msg or "connected" in error_msg

        # No AI call, no state update
        mock_gemini_for_loop.generate_structured.assert_not_called()
        mock_state_manager_e2e.update_state.assert_not_called()
