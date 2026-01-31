"""Rules engine for aggregating and executing rules."""
from typing import List, Dict, Any, Optional

from app.core.rules.base_rule import BaseRule, RuleResult
from app.models.action import PlayerAction, ActionDefinition, ActionRequirement
from app.models.game_state import GameState


class RulesEngine:
    """Aggregates and executes game rules."""

    def __init__(self, game_data_loader=None):
        """
        Initialize rules engine.

        Args:
            game_data_loader: GameDataLoader or None. If provided, enables
                ResourceAvailabilityRule, LocationTopologyRule, AtmosphereAccessRule,
                and LocationSealRule with real checks.
                If None, only a no-op ResourceAvailabilityRule is registered (always valid).
        """
        self.rules: List[BaseRule] = []
        from app.core.rules.resource_rules import ResourceAvailabilityRule
        from app.core.rules.location_rules import (
            LocationTopologyRule,
            AtmosphereAccessRule,
            LocationSealRule,
        )
        from app.core.rules.npc_rules import NPCInteractionRule

        if game_data_loader is not None:
            # Register rules in priority order (higher priority = checked first)
            self.register_rule(LocationSealRule(game_data_loader))      # Priority 10
            self.register_rule(AtmosphereAccessRule(game_data_loader))  # Priority 5
            self.register_rule(ResourceAvailabilityRule(game_data_loader))
            self.register_rule(LocationTopologyRule(game_data_loader))
        else:
            self.register_rule(ResourceAvailabilityRule())
        
        # Always register NPC interaction rule
        self.register_rule(NPCInteractionRule())

    def register_rule(self, rule: BaseRule):
        """
        Register a rule with the engine.

        Args:
            rule: Rule instance to register
        """
        self.rules.append(rule)

    def register_rules(self, rules: List[BaseRule]):
        """
        Register multiple rules.

        Args:
            rules: List of rule instances
        """
        self.rules.extend(rules)

    async def validate_action(self, game_state: GameState, action: PlayerAction) -> RuleResult:
        """
        Validate action against all applicable rules.

        Args:
            game_state: Current GameState
            action: PlayerAction to validate

        Returns:
            RuleResult: Aggregated validation result
        """
        for rule in self.rules:
            result = rule.validate(action, game_state) 
            if not result.valid:
                return result
        
        return RuleResult(valid=True)

    async def apply_rules(self, game_state, context: dict) -> List[RuleResult]:
        """
        Apply all applicable rules.

        Args:
            game_state: Current GameState
            context: Application context

        Returns:
            List[RuleResult]: Results from all applied rules
        """
        raise NotImplementedError

    def get_rules_by_type(self, rule_type: type) -> List[BaseRule]:
        """
        Get all rules of a specific type.

        Args:
            rule_type: Rule class type

        Returns:
            List[BaseRule]: Matching rules
        """
        raise NotImplementedError

    def clear_rules(self):
        """Clear all registered rules."""
        self.rules = []

    def check_action_availability(
        self,
        action_def: ActionDefinition,
        game_state: GameState
    ) -> tuple[bool, Optional[str]]:
        """
        Check if an action definition is available for the current game state.
        
        This is used for filtering which actions to show to the player,
        NOT for validating player-submitted actions.
        
        Args:
            action_def: The action definition to check
            game_state: Current game state
            
        Returns:
            Tuple of (is_available, reason_if_not_available)
        """
        req = action_def.requirements
        player = game_state.player
        world = game_state.world
        resources = world.resources
        
        # 1. Location requirement
        if req.location and req.location != "":
            player_loc = player.location
            # Support comma-separated locations or exact match
            allowed_locations = [loc.strip() for loc in req.location.split(",")]
            if player_loc not in allowed_locations:
                return False, f"Requires location: {req.location}"
        
        # 2. Minimum resource levels
        for resource_name, min_val in (req.min_resource_levels or {}).items():
            resource = getattr(resources, resource_name, None)
            if resource is None:
                continue
            current = resource.current if hasattr(resource, 'current') else resource
            if isinstance(current, (int, float)) and current < min_val:
                return False, f"Insufficient {resource_name}: need {min_val}"
        
        # 3. Required items in inventory
        player_inventory = player.inventory or []
        for item in (req.items or []):
            if item not in player_inventory:
                return False, f"Missing item: {item}"
        
        # 4. NPC must be present at player's location
        # Match by prefix (e.g., "npc_captain" matches "npc_captain_2961")
        if req.npc_present and req.npc_present != "":
            npcs_at_location = game_state.get_npcs_at_player_location()
            npc_ids = [n.id for n in npcs_at_location]
            
            # Check exact match or prefix match
            found = False
            for npc_id in npc_ids:
                if npc_id == req.npc_present or npc_id.startswith(req.npc_present + "_"):
                    found = True
                    break
            
            if not found:
                return False, f"NPC '{req.npc_present}' not present"
        
        # 5. Required flags
        player_flags = player.flags or {}
        for flag_name, flag_value in (req.required_flags or {}).items():
            if player_flags.get(flag_name) != flag_value:
                return False, f"Requires flag '{flag_name}' = {flag_value}"
        
        # 6. Minimum health
        if req.min_health is not None:
            player_health = getattr(player, 'health', 100)
            if player_health < req.min_health:
                return False, f"Health too low: need {req.min_health}"
        
        # 7. Maximum stress
        if req.max_stress is not None:
            player_stress = getattr(player, 'stress', 0)
            if player_stress > req.max_stress:
                return False, f"Too stressed: max {req.max_stress}"
        
        # 8. Cooldown check (if game state tracks action cooldowns)
        if action_def.cooldown > 0 and hasattr(player, 'action_cooldowns'):
            cooldowns = player.action_cooldowns or {}
            remaining = cooldowns.get(action_def.id, 0)
            if remaining > 0:
                return False, f"On cooldown: {remaining} turns"
        
        # 9. One-time action check
        if action_def.one_time and hasattr(player, 'completed_actions'):
            completed = player.completed_actions or []
            if action_def.id in completed:
                return False, "Already completed (one-time action)"
        
        return True, None

    def filter_available_actions(
        self,
        all_actions: List[ActionDefinition],
        game_state: GameState
    ) -> List[ActionDefinition]:
        """
        Filter a list of action definitions to only those available in current state.
        
        Args:
            all_actions: List of all possible action definitions
            game_state: Current game state
            
        Returns:
            List of available action definitions
        """
        available = []
        for action_def in all_actions:
            is_available, _ = self.check_action_availability(action_def, game_state)
            if is_available:
                available.append(action_def)
        return available

    def get_action_unavailability_reasons(
        self,
        all_actions: List[ActionDefinition],
        game_state: GameState
    ) -> Dict[str, str]:
        """
        Get reasons why each unavailable action is not available.
        
        Args:
            all_actions: List of all possible action definitions
            game_state: Current game state
            
        Returns:
            Dict mapping action_id to reason string (only for unavailable actions)
        """
        reasons = {}
        for action_def in all_actions:
            is_available, reason = self.check_action_availability(action_def, game_state)
            if not is_available and reason:
                reasons[action_def.id] = reason
        return reasons