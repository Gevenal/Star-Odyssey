"""NPC interaction rules."""
from app.core.rules.base_rule import BaseRule, RuleResult
from app.models.action import PlayerAction
from app.models.game_state import GameState


class NPCInteractionRule(BaseRule):
    """Rule for player-NPC interactions."""

    def validate(self, action: PlayerAction, game_state: GameState) -> RuleResult:
        """
        Validate NPC interaction action.

        Checks:
        - Target NPC exists
        - Target NPC is alive
        - Player and NPC are in same location (if action requires proximity)
        """
        # Only validate if action targets an NPC
        if not action.target_npc:
            return RuleResult(valid=True)
        
        npc_id = action.target_npc
        npc = game_state.npcs.get(npc_id)
        
        if not npc:
            return RuleResult(
                valid=False,
                error=f"NPC {npc_id} not found",
                suggestion="Check if NPC ID is correct"
            )
        
        if not npc.alive:
            return RuleResult(
                valid=False,
                error=f"{npc.name} is not available",
                suggestion="This NPC is no longer alive"
            )
        
        # Check if action requires same location (e.g., talking)
        if action.action_id in ["talk_to_npc", "interact_with_npc"]:
            if npc.location != game_state.player.location:
                return RuleResult(
                    valid=False,
                    error=f"{npc.name} is not at your location",
                    suggestion=f"Move to {npc.location} to interact"
                )
        
        return RuleResult(valid=True)

    def apply(self, game_state: GameState, context: dict) -> RuleResult:
        """
        Apply interaction effects (e.g., update relationship).

        This is called after validation passes and action is executed.
        """
        # NPC interaction effects are typically handled by AI response
        # (npc_reactions in GameActionResponse)
        # This method can be used for additional side effects if needed
        return RuleResult(valid=True)


class NPCTrustRule(BaseRule):
    """Rule for NPC trust/relationship management."""

    def validate(self, action: PlayerAction, game_state: GameState) -> RuleResult:
        """
        Validate trust changes.

        Currently, trust changes are handled by AI response,
        so this just validates that trust changes are within bounds.
        """
        # Trust changes are applied via AI response (npc_reactions),
        # so validation happens at that level
        return RuleResult(valid=True)

    def apply(self, game_state: GameState, context: dict) -> RuleResult:
        """
        Apply trust updates.

        Args:
            game_state: Current GameState
            context: Should contain 'npc_id' and 'trust_delta'
        """
        npc_id = context.get("npc_id")
        trust_delta = context.get("trust_delta", 0)
        
        if not npc_id or npc_id not in game_state.npcs:
            return RuleResult(valid=False, error=f"NPC {npc_id} not found")
        
        npc = game_state.npcs[npc_id]
        
        # Get or create relationship with player
        if "player" not in npc.relationships:
            from app.models.npc import NPCRelationship
            npc.relationships["player"] = NPCRelationship(
                target_npc_id="player",
                trust_level=0,
                relationship_history=[]
            )
        
        rel = npc.relationships["player"]
        new_trust = rel.trust_level + trust_delta
        new_trust = max(-100, min(100, new_trust))  # Clamp to -100..100
        
        rel.trust_level = new_trust
        
        # Add to history if significant change
        if abs(trust_delta) >= 10:
            action_desc = context.get("action_description", "interaction")
            rel.relationship_history.append(f"Trust changed by {trust_delta} due to: {action_desc}")
            # Keep history limited
            if len(rel.relationship_history) > 10:
                rel.relationship_history = rel.relationship_history[-10:]
        
        return RuleResult(valid=True, metadata={"new_trust_level": new_trust})


class NPCBehaviorRule(BaseRule):
    """Rule for autonomous NPC behavior validation."""

    def validate(self, action: PlayerAction, game_state: GameState) -> RuleResult:
        """
        Validate NPC action (for autonomous NPC behavior).

        This is not used for player actions, but for validating
        NPC autonomous actions before they're applied.
        """
        # NPC autonomous actions are validated in NPCScheduler
        # This rule is for future use if needed
        return RuleResult(valid=True)

    def apply(self, game_state: GameState, context: dict) -> RuleResult:
        """
        Apply NPC action effects.

        Args:
            game_state: Current GameState
            context: Should contain 'npc_id' and 'action_result'
        """
        npc_id = context.get("npc_id")
        action_result = context.get("action_result", {})
        
        if not npc_id or npc_id not in game_state.npcs:
            return RuleResult(valid=False, error=f"NPC {npc_id} not found")
        
        npc = game_state.npcs[npc_id]
        state_changes = action_result.get("state_changes", {})
        
        # Apply state changes
        if "current_activity" in state_changes:
            npc.current_activity = state_changes["current_activity"]
        if "stress_level" in state_changes:
            npc.stress_level = max(0, min(100, state_changes["stress_level"]))
            npc.update_breakdown_state()  # Update breakdown state
        if "location" in state_changes:
            npc.location = state_changes["location"]
        
        return RuleResult(valid=True)
