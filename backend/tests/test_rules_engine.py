"""Tests for rules engine."""
import pytest
from app.core.rules.engine import RulesEngine
from app.core.rules.base_rule import BaseRule, RuleResult
from app.core.rules.resource_rules import ResourceAvailabilityRule, ResourceDecayRule, CriticalResourceRule
from app.core.rules.location_rules import LocationTopologyRule, AtmosphereAccessRule, LocationSealRule
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

    def test_atmosphere_safe(self, sample_game_state, sample_player_action):
        """Test access to location with safe atmosphere."""
        from unittest.mock import MagicMock
        from app.core.rules.location_rules import AtmosphereAccessRule

        loader = MagicMock()
        loc = MagicMock()
        loc.default_atmosphere = "normal"
        loader.load_world_config.return_value = MagicMock(
            locations={"med_bay": loc}
        )

        gs = sample_game_state.model_copy(deep=True)
        act = sample_player_action.model_copy(deep=True)
        act.target_location = "med_bay"

        rule = AtmosphereAccessRule(loader)
        result = rule.validate(act, gs)
        assert result.valid is True

    def test_atmosphere_requires_equipment(self, sample_game_state, sample_player_action):
        """Test vacuum/toxic atmosphere requires protective equipment."""
        from unittest.mock import MagicMock
        from app.core.rules.location_rules import AtmosphereAccessRule

        loader = MagicMock()
        loc = MagicMock()
        loc.default_atmosphere = "vacuum"
        loader.load_world_config.return_value = MagicMock(
            locations={"airlock": loc}
        )

        gs = sample_game_state.model_copy(deep=True)
        gs.player.inventory = []  # No space suit
        act = sample_player_action.model_copy(deep=True)
        act.target_location = "airlock"

        rule = AtmosphereAccessRule(loader)
        result = rule.validate(act, gs)
        assert result.valid is False
        assert "vacuum" in (result.error or "").lower() or "space suit" in (result.error or "").lower()

    def test_atmosphere_with_equipment_passes(self, sample_game_state, sample_player_action):
        """Test vacuum access succeeds with space suit."""
        from unittest.mock import MagicMock
        from app.core.rules.location_rules import AtmosphereAccessRule

        loader = MagicMock()
        loc = MagicMock()
        loc.default_atmosphere = "vacuum"
        loader.load_world_config.return_value = MagicMock(
            locations={"airlock": loc}
        )

        gs = sample_game_state.model_copy(deep=True)
        gs.player.inventory = ["space_suit"]
        act = sample_player_action.model_copy(deep=True)
        act.target_location = "airlock"

        rule = AtmosphereAccessRule(loader)
        result = rule.validate(act, gs)
        assert result.valid is True

    def test_seal_rule_open_location(self, sample_game_state, sample_player_action):
        """Test access to open (unsealed) location."""
        from unittest.mock import MagicMock
        from app.core.rules.location_rules import LocationSealRule

        loader = MagicMock()
        gs = sample_game_state.model_copy(deep=True)
        act = sample_player_action.model_copy(deep=True)
        act.target_location = "med_bay"

        rule = LocationSealRule(loader)
        result = rule.validate(act, gs)
        assert result.valid is True


class TestResourceDecayRule:
    """Test suite for resource decay rule."""

    def test_decay_applies_correctly(self, sample_game_state):
        """Test that decay is applied correctly to resources."""
        from app.core.rules.resource_rules import ResourceDecayRule

        rule = ResourceDecayRule()
        gs = sample_game_state.model_copy(deep=True)
        gs.world.resources.oxygen_level.current = 85.0

        _, changes = rule.apply_decay(gs)

        # Oxygen should have decayed by its rate (1.2)
        assert "oxygen_level" in changes
        assert changes["oxygen_level"]["old"] == 85.0
        assert changes["oxygen_level"]["new"] == 85.0 - 1.2

    def test_decay_respects_min_value(self, sample_game_state):
        """Test that decay doesn't go below minimum."""
        from app.core.rules.resource_rules import ResourceDecayRule

        rule = ResourceDecayRule()
        gs = sample_game_state.model_copy(deep=True)
        gs.world.resources.oxygen_level.current = 0.5  # Very low

        _, changes = rule.apply_decay(gs)

        if "oxygen_level" in changes:
            assert changes["oxygen_level"]["new"] >= 0.0


class TestCriticalResourceRule:
    """Test suite for critical resource rule."""

    def test_detect_critical_resources(self, sample_game_state):
        """Test detection of critical resource levels."""
        from app.core.rules.resource_rules import CriticalResourceRule

        rule = CriticalResourceRule()
        gs = sample_game_state.model_copy(deep=True)
        gs.world.resources.oxygen_level.current = 15.0  # Below critical threshold (25)

        result = rule.validate(gs)

        assert result.valid is True
        assert result.metadata is not None
        assert "oxygen_level" in result.metadata.get("critical_resources", [])
        assert result.metadata.get("has_critical") is True

    def test_detect_depleted_resources(self, sample_game_state):
        """Test detection of depleted (zero) resources."""
        from app.core.rules.resource_rules import CriticalResourceRule

        rule = CriticalResourceRule()
        gs = sample_game_state.model_copy(deep=True)
        gs.world.resources.oxygen_level.current = 0.0

        result = rule.validate(gs)

        assert result.metadata is not None
        assert "oxygen_level" in result.metadata.get("depleted_resources", [])

    def test_game_over_oxygen_depletion(self, sample_game_state):
        """Test game over condition when oxygen is depleted."""
        from app.core.rules.resource_rules import CriticalResourceRule

        rule = CriticalResourceRule()
        gs = sample_game_state.model_copy(deep=True)
        gs.world.resources.oxygen_level.current = 0.0

        should_end, ending_id = rule.check_game_over_conditions(gs)

        assert should_end is True
        assert ending_id == "ending_oxygen_depletion"

    def test_normal_resources_no_critical(self, sample_game_state):
        """Test normal resource levels don't trigger critical."""
        from app.core.rules.resource_rules import CriticalResourceRule

        rule = CriticalResourceRule()
        gs = sample_game_state.model_copy(deep=True)
        gs.world.resources.oxygen_level.current = 80.0

        result = rule.validate(gs)

        assert result.metadata is not None
        assert "oxygen_level" not in result.metadata.get("critical_resources", [])


class TestAIOutputValidation:
    """Test suite for AI output validation in GameLoop."""

    def test_validate_ai_output_removes_invalid_npc(self, sample_game_state):
        """Test AI output validation removes reactions for invalid NPCs."""
        from app.ai.validators.output_validator import AIOutputValidator, GameContext
        from app.ai.schemas.game_response import (
            GameActionResponse as AIGameActionResponse,
            NPCReaction,
            Mood,
            ConfidenceLevel,
        )

        validator = AIOutputValidator()

        ai_resp = AIGameActionResponse(
            success=True,
            narration="Test narration",
            mood=Mood.TENSE,
            confidence_level=ConfidenceLevel.HIGH,
            state_changes=[],
            resource_changes=[],
            npc_reactions=[
                NPCReaction(
                    npc_id="invalid_npc",  # Non-existent NPC
                    reaction_text="This NPC doesn't exist",
                    disposition_change=5,
                    new_activity=None
                )
            ],
            available_actions=[],
            trigger_ending=False,
            ending_id=None,
        )

        context = GameContext(
            valid_npcs={"test_npc_001"},  # Only valid NPC
            valid_locations={"med_bay", "bridge"},
            valid_items=set(),
            discovered_secrets=set(),
            player_inventory=set(),
            player_location="bridge",
            current_day=3,
            npc_alive_status={"test_npc_001": True},
            allow_death=False,
        )

        result = validator.validate(ai_resp, context)

        # Should have errors about invalid NPC
        assert not result.valid or len(result.errors) > 0
        has_npc_error = any("invalid_npc" in (e.value or "") or "NPC" in (e.message or "") for e in result.errors)
        assert has_npc_error

    def test_auto_correct_removes_invalid_reactions(self, sample_game_state):
        """Test auto-correct removes invalid NPC reactions."""
        from app.ai.validators.output_validator import AIOutputValidator, GameContext, ValidationResult
        from app.ai.schemas.game_response import (
            GameActionResponse as AIGameActionResponse,
            NPCReaction,
            Mood,
            ConfidenceLevel,
        )

        validator = AIOutputValidator()

        ai_resp = AIGameActionResponse(
            success=True,
            narration="Test narration",
            mood=Mood.TENSE,
            confidence_level=ConfidenceLevel.HIGH,
            state_changes=[],
            resource_changes=[],
            npc_reactions=[
                NPCReaction(
                    npc_id="invalid_npc",
                    reaction_text="This NPC doesn't exist",
                    disposition_change=5,
                    new_activity=None
                ),
                NPCReaction(
                    npc_id="test_npc_001",  # Valid NPC
                    reaction_text="Valid NPC reaction",
                    disposition_change=10,
                    new_activity="Working"
                )
            ],
            available_actions=[],
            trigger_ending=False,
            ending_id=None,
        )

        context = GameContext(
            valid_npcs={"test_npc_001"},
            valid_locations={"med_bay", "bridge"},
            valid_items=set(),
            discovered_secrets=set(),
            player_inventory=set(),
            player_location="bridge",
            current_day=3,
            npc_alive_status={"test_npc_001": True},
            allow_death=False,
        )

        result = validator.validate(ai_resp, context)
        corrected = validator.auto_correct(ai_resp, context, result)

        # Should have removed invalid NPC but kept valid one
        assert len(corrected.npc_reactions) == 1
        assert corrected.npc_reactions[0].npc_id == "test_npc_001"

    def test_validate_blocks_early_ending(self):
        """Test validation warns about early ending trigger."""
        from app.ai.validators.output_validator import AIOutputValidator, GameContext
        from app.ai.schemas.game_response import (
            GameActionResponse as AIGameActionResponse,
            Mood,
            ConfidenceLevel,
        )

        validator = AIOutputValidator()

        ai_resp = AIGameActionResponse(
            success=True,
            narration="Test narration",
            mood=Mood.TENSE,
            confidence_level=ConfidenceLevel.HIGH,
            state_changes=[],
            resource_changes=[],
            npc_reactions=[],
            available_actions=[],
            trigger_ending=True,  # Trying to end game early
            ending_id="early_ending",
        )

        context = GameContext(
            valid_npcs=set(),
            valid_locations=set(),
            valid_items=set(),
            discovered_secrets=set(),
            player_inventory=set(),
            player_location="bridge",
            current_day=2,  # Early day - ending shouldn't trigger
            npc_alive_status={},
            allow_death=False,
        )

        result = validator.validate(ai_resp, context)

        # Should have warning about early ending
        has_early_warning = any("early" in (w.message or "").lower() for w in result.warnings)
        assert has_early_warning

    def test_validate_clamps_large_resource_changes(self):
        """Test validation warns about large resource changes."""
        from app.ai.validators.output_validator import AIOutputValidator, GameContext
        from app.ai.schemas.game_response import (
            GameActionResponse as AIGameActionResponse,
            ResourceChange,
            Mood,
            ConfidenceLevel,
        )

        validator = AIOutputValidator()

        ai_resp = AIGameActionResponse(
            success=True,
            narration="Test narration",
            mood=Mood.TENSE,
            confidence_level=ConfidenceLevel.HIGH,
            state_changes=[],
            resource_changes=[
                ResourceChange(
                    resource_name="oxygen_level",
                    change_amount=50,  # Too large
                    reason="Magic oxygen"
                )
            ],
            npc_reactions=[],
            available_actions=[],
            trigger_ending=False,
            ending_id=None,
        )

        context = GameContext(
            valid_npcs=set(),
            valid_locations=set(),
            valid_items=set(),
            discovered_secrets=set(),
            player_inventory=set(),
            player_location="bridge",
            current_day=3,
            npc_alive_status={},
            allow_death=False,
            resource_levels={"oxygen_level": 50.0},
        )

        result = validator.validate(ai_resp, context)

        # Should have warning about large change
        has_large_warning = any("large" in (w.message or "").lower() for w in result.warnings)
        assert has_large_warning
