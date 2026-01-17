"""Tests for game loop."""
import pytest
from app.core.game_loop import GameLoop


class TestGameLoop:
    """Test suite for main game loop."""

    @pytest.mark.asyncio
    async def test_initialize_game(self, mock_gemini_client, mock_game_data_loader):
        """Test game initialization."""
        # TODO: Implement
        # loop = GameLoop(gemini_client, game_data_loader)
        # state = await loop.initialize_game("Player Name")
        # assert state.phase == GamePhase.INTRO
        # assert state.player.name == "Player Name"
        pass

    @pytest.mark.asyncio
    async def test_process_player_action(self, sample_game_state, sample_player_action):
        """Test processing player action."""
        # TODO: Implement
        # response = await loop.process_action(sample_player_action, sample_game_state)
        # assert response.success
        # assert response.narration
        pass

    @pytest.mark.asyncio
    async def test_turn_phases(self, sample_game_state):
        """Test turn phase progression."""
        # TODO: Test each phase executes in order
        # world_update -> event_generation -> npc_actions -> player_turn -> consequence -> end_check
        pass

    @pytest.mark.asyncio
    async def test_resource_decay(self, sample_game_state):
        """Test resources decay each turn."""
        # TODO: Run turn
        # Verify resources decreased by decay_rate
        pass

    @pytest.mark.asyncio
    async def test_game_ending_trigger(self, sample_game_state):
        """Test game ending triggers correctly."""
        # TODO: Set state to trigger ending
        # Process turn
        # Verify phase changes to ENDING
        pass
