"""Tests for rules engine."""
import pytest
from app.core.rules.engine import RulesEngine
from app.core.rules.base_rule import BaseRule, RuleResult
from app.core.rules.resource_rules import ResourceAvailabilityRule
from app.core.rules.location_rules import LocationTopologyRule
from app.models.action import PlayerAction


class _AlwaysFailRule(BaseRule):
    """Rule that always returns invalid (for testing short-circuit and 400 path)."""

    def validate(self, action: PlayerAction, game_state) -> RuleResult:
        return RuleResult(valid=False, error="Rejected by test rule", suggestion="Do something else")


class TestRulesEngine:
    """Test suite for rules engine."""

    @pytest.mark.asyncio
    async def test_validate_action_success(self, sample_game_state, sample_player_action):
        """With current rules (ResourceAvailabilityRule always True), validation passes."""
        engine = RulesEngine()
        result = await engine.validate_action(sample_game_state, sample_player_action)
        assert result.valid is True
        assert result.error is None

    @pytest.mark.asyncio
    async def test_validate_action_fail_short_circuit(self, sample_game_state, sample_player_action):
        """When a rule returns valid=False, engine returns that result and stops (short-circuit)."""
        engine = RulesEngine()
        engine.clear_rules()
        engine.register_rule(_AlwaysFailRule())
        result = await engine.validate_action(sample_game_state, sample_player_action)
        assert result.valid is False
        assert result.error == "Rejected by test rule"
        assert result.suggestion == "Do something else"

    @pytest.mark.asyncio
    async def test_validate_action_fail_then_pass(self, sample_game_state, sample_player_action):
        """First rule fails → result is invalid; if we remove fail rule, default passes."""
        engine = RulesEngine()
        engine.clear_rules()
        engine.register_rule(_AlwaysFailRule())
        engine.register_rule(ResourceAvailabilityRule())
        result = await engine.validate_action(sample_game_state, sample_player_action)
        assert result.valid is False
        assert "Rejected by test rule" in (result.error or "")


class TestResourceRules:
    """Test suite for resource-related rules."""

    def test_resource_availability_sufficient(self, sample_game_state, sample_player_action):
        """Resource check passes when location matches and no extra requirements."""
        from unittest.mock import MagicMock
        from app.core.rules.resource_rules import ResourceAvailabilityRule

        req = MagicMock()
        req.location = "command_bridge"
        req.min_resource_levels = {}
        req.items = []
        req.npc_present = None
        req.required_flags = {}
        loader = MagicMock()
        loader.get_action.return_value = MagicMock(requirements=req)

        gs = sample_game_state.model_copy(deep=True)
        gs.player.location = "command_bridge"
        act = sample_player_action.model_copy(deep=True)
        act.action_id = "check_systems"

        rule = ResourceAvailabilityRule(loader)
        result = rule.validate(act, gs)
        assert result.valid is True

    def test_resource_availability_insufficient_location(self, sample_game_state, sample_player_action):
        """Resource check fails when required location does not match."""
        from unittest.mock import MagicMock
        from app.core.rules.resource_rules import ResourceAvailabilityRule

        req = MagicMock()
        req.location = "command_bridge"
        req.min_resource_levels = {}
        req.items = []
        req.npc_present = None
        req.required_flags = {}
        loader = MagicMock()
        loader.get_action.return_value = MagicMock(requirements=req)

        gs = sample_game_state.model_copy(deep=True)
        gs.player.location = "cryo_bay"
        act = sample_player_action.model_copy(deep=True)
        act.action_id = "check_systems"

        rule = ResourceAvailabilityRule(loader)
        result = rule.validate(act, gs)
        assert result.valid is False
        assert "command_bridge" in (result.error or "")
        assert "cryo_bay" in (result.error or "")

    def test_resource_availability_insufficient_resources(self, sample_game_state, sample_player_action):
        """Resource check fails when min_resource_levels not met."""
        from unittest.mock import MagicMock
        from app.core.rules.resource_rules import ResourceAvailabilityRule

        req = MagicMock()
        req.location = None
        req.min_resource_levels = {"oxygen_level": 99.0}
        req.items = []
        req.npc_present = None
        req.required_flags = {}
        loader = MagicMock()
        loader.get_action.return_value = MagicMock(requirements=req)

        gs = sample_game_state.model_copy(deep=True)
        gs.world.resources.oxygen_level = gs.world.resources.oxygen_level.model_copy(update={"current": 50.0})
        act = sample_player_action.model_copy(deep=True)
        act.action_id = "repair_act"

        rule = ResourceAvailabilityRule(loader)
        result = rule.validate(act, gs)
        assert result.valid is False
        assert "oxygen_level" in (result.error or "") and "99" in (result.error or "")

    def test_resource_availability_no_loader_always_valid(self, sample_game_state, sample_player_action):
        """Without loader, ResourceAvailabilityRule always returns valid."""
        from app.core.rules.resource_rules import ResourceAvailabilityRule

        rule = ResourceAvailabilityRule()
        result = rule.validate(sample_player_action, sample_game_state)
        assert result.valid is True


class TestLocationRules:
    """Test suite for location-related rules."""

    def test_topology_connected_locations(self, sample_game_state, sample_player_action):
        """Movement between connected locations is allowed."""
        from unittest.mock import MagicMock
        from app.core.rules.location_rules import LocationTopologyRule

        loader = MagicMock()
        loc = MagicMock()
        loc.connected_to = ["crew_quarters", "med_bay"]
        loader.load_world_config.return_value = MagicMock(locations={"cryo_bay": loc})

        gs = sample_game_state.model_copy(deep=True)
        gs.player.location = "cryo_bay"
        act = sample_player_action.model_copy(deep=True)
        act.target_location = "med_bay"

        rule = LocationTopologyRule(loader)
        result = rule.validate(act, gs)
        assert result.valid is True

    def test_topology_disconnected_locations(self, sample_game_state, sample_player_action):
        """Movement to non-adjacent location is rejected."""
        from unittest.mock import MagicMock
        from app.core.rules.location_rules import LocationTopologyRule

        loader = MagicMock()
        loc = MagicMock()
        loc.connected_to = ["crew_quarters", "med_bay"]
        loader.load_world_config.return_value = MagicMock(locations={"cryo_bay": loc})

        gs = sample_game_state.model_copy(deep=True)
        gs.player.location = "cryo_bay"
        act = sample_player_action.model_copy(deep=True)
        act.target_location = "engineering"

        rule = LocationTopologyRule(loader)
        result = rule.validate(act, gs)
        assert result.valid is False
        assert "engineering" in (result.error or "") and "cryo_bay" in (result.error or "")
        assert "crew_quarters" in (result.suggestion or "") or "med_bay" in (result.suggestion or "")

    def test_topology_no_target_skipped(self, sample_game_state, sample_player_action):
        """If target_location is None, topology rule passes (no movement)."""
        from unittest.mock import MagicMock
        from app.core.rules.location_rules import LocationTopologyRule

        loader = MagicMock()
        rule = LocationTopologyRule(loader)
        act = sample_player_action.model_copy(deep=True)
        act.target_location = None
        result = rule.validate(act, sample_game_state)
        assert result.valid is True
        loader.load_world_config.assert_not_called()

    def test_atmosphere_safe(self, sample_game_state):
        """Test access to location with safe atmosphere."""
        # TODO: Implement
        pass

    def test_atmosphere_requires_equipment(self, sample_game_state):
        """Test vacuum/toxic atmosphere requires protective equipment."""
        # TODO: Implement
        pass


class TestAIOutputValidation:
    """Test suite for AI output validation."""

    def test_validate_ai_output_forbidden_behavior(self):
        """Test AI output validation catches forbidden behaviors."""
        # TODO: Create AI output suggesting forbidden action
        # Verify it's rejected
        pass

    def test_validate_ai_output_valid_state_changes(self):
        """Test valid state changes pass validation."""
        # TODO: Implement
        pass

    def test_validate_ai_output_invalid_state_changes(self):
        """Test invalid state changes are rejected."""
        # TODO: Create invalid state change (e.g., negative resource)
        # Verify rejection
        pass
