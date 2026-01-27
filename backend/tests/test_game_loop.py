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
