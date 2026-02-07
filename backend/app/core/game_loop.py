"""Game loop orchestration."""
from typing import AsyncGenerator, Dict, Any, Optional, Tuple
import random

from app.models.action import PlayerAction
from app.models.response import (
    GameActionResponse,
    ResourceChange,
    StateChange as StateChangeModel,
    NPCReaction as NPCReactionModel,
)
from app.models.enums import Mood
from app.core.game_state_manager import GameStateManager
from app.utils.state_converter import StateConverter
from app.ai.prompts.narrator import build_narrator_prompt, get_narrator_system_instruction
from app.ai.schemas.game_response import (
    GameActionResponse as AIGameActionResponse,
    Mood as AIMood,
    ConfidenceLevel as AIConfidenceLevel,
)
from app.ai.validators.output_validator import AIOutputValidator, GameContext
from app.ai.exceptions import GeminiAPIError
from app.core.rules.resource_rules import ResourceDecayRule, CriticalResourceRule
from app.utils.logger import get_logger

logger = get_logger(__name__)


def _parse_value(s: str) -> Any:
    """Coerce AI string to int/float/bool for state updates."""
    if not isinstance(s, str):
        return s
    v = s.strip().lower()
    if v in ("true", "yes", "1"):
        return True
    if v in ("false", "no", "0"):
        return False
    try:
        return int(s)
    except ValueError:
        pass
    try:
        return float(s)
    except ValueError:
        pass
    return s


def _is_quota_error(exc: Exception) -> bool:
    """Return True when Gemini error indicates quota/rate limit."""
    message = str(exc).lower()
    if "quota" in message or "rate limit" in message or "429" in message:
        return True
    original = getattr(exc, "original_error", None)
    if original is not None:
        original_message = str(original).lower()
        return "quota" in original_message or "rate limit" in original_message or "429" in original_message
    return False


def _build_quota_fallback(action: PlayerAction) -> AIGameActionResponse:
    """Create an in-universe response when Gemini quota is exceeded."""
    narration = (
        f"You {action.action_text}. The ship's external processing link throttles, "
        "and ORACLE's response arrives only as static and delay. "
        "Warning lights pulse softly in the silence."
    )
    return AIGameActionResponse(
        success=True,
        narration=narration,
        mood=AIMood.TENSE,
        confidence_level=AIConfidenceLevel.SPECULATIVE,
        state_changes=[],
        resource_changes=[],
        npc_reactions=[],
        available_actions=["check_systems", "talk_to_oracle", "explore_bridge"],
        trigger_ending=False,
        ending_id=None,
        oracle_message="External computation link is rate-limited. Please try again shortly.",
    )


def _build_generic_fallback(action: PlayerAction) -> AIGameActionResponse:
    """Fallback when AI fails for unknown reasons."""
    return AIGameActionResponse(
        success=True,
        narration=f"You {action.action_text}. The ship's systems hum in the background.",
        mood=AIMood.TENSE,
        confidence_level=AIConfidenceLevel.MEDIUM,
        state_changes=[],
        resource_changes=[],
        npc_reactions=[],
        available_actions=["check_systems", "talk_to_oracle", "explore_bridge"],
        trigger_ending=False,
        ending_id=None,
    )


def _entity_path(entity_type: str, entity_id: Optional[str], field: str) -> Optional[str]:
    """Map entity_type + entity_id + field to GameStateManager dotted path."""
    et = (entity_type or "").lower()
    if et == "player":
        return f"player.{field}"
    if et == "npc" and entity_id:
        return f"npcs.{entity_id}.{field}"
    if et == "world":
        return f"crew_collective.{field}"
    if et == "location" and entity_id:
        return f"locations.{entity_id}.{field}"
    return None


def _ai_to_model(ai: AIGameActionResponse) -> GameActionResponse:
    """Convert AI schema GameActionResponse to api models.response GameActionResponse."""
    resource_changes = [
        ResourceChange(
            resource_name=c.resource_name,
            change_amount=c.change_amount,
            reason=c.reason,
        )
        for c in (ai.resource_changes or [])
    ]
    state_changes = [
        StateChangeModel(
            entity_type=sc.entity_type.value if hasattr(sc.entity_type, "value") else str(sc.entity_type),
            entity_id=sc.entity_id or "",
            field=sc.field,
            old_value=None,
            new_value=sc.new_value,
            reason=sc.reason,
        )
        for sc in (ai.state_changes or [])
    ]
    npc_reactions = [
        NPCReactionModel(
            npc_id=r.npc_id,
            reaction_text=r.reaction_text,
            disposition_change=r.disposition_change,
            new_activity=r.new_activity,
        )
        for r in (ai.npc_reactions or [])
    ]
    mood_val = ai.mood.value if hasattr(ai.mood, "value") else getattr(ai.mood, "value", str(ai.mood))
    try:
        mood = Mood(mood_val)
    except ValueError:
        mood = Mood.TENSE

    return GameActionResponse(
        success=ai.success,
        narration=ai.narration,
        resource_changes=resource_changes,
        state_changes=state_changes,
        npc_reactions=npc_reactions,
        available_actions=ai.available_actions or [],
        mood=mood,
        trigger_ending=ai.trigger_ending or False,
        ending_id=ai.ending_id,
        oracle_message=ai.oracle_message,
        confidence_level=getattr(ai.confidence_level, "value", str(ai.confidence_level)) or "high",
    )


class GameLoop:
    """Orchestrates the turn-based game loop."""

    def __init__(self, state_manager, rules_engine, gemini_client, game_data_loader=None):
        """
        Initialize game loop with dependencies.

        Args:
            state_manager: SessionStateManager
            rules_engine: RulesEngine
            gemini_client: GeminiClient
            game_data_loader: Optional GameDataLoader for resource rules
        """
        self.state_manager = state_manager
        self.rules_engine = rules_engine
        self.gemini_client = gemini_client
        self.game_data_loader = game_data_loader

        # Initialize AI output validator
        self.ai_validator = AIOutputValidator()

        # Initialize resource rules
        self.decay_rule = ResourceDecayRule(game_data_loader)
        self.critical_rule = CriticalResourceRule(game_data_loader)

        # Initialize NPC scheduler
        from app.ai.agents.npc_scheduler import NPCScheduler
        self.npc_scheduler = NPCScheduler(gemini_client=gemini_client)

    async def initialize(self, player_name: str) -> Tuple[str, Dict[str, Any]]:
        """
        Start a new game session.

        Args:
            player_name: Player's chosen name

        Returns:
            (session_id, initial_snapshot)
        """
        session_id = await self.state_manager.create_session(player_name)
        snapshot = await self.state_manager.get_state(session_id)
        return session_id, snapshot

    async def process_action(self, session_id: str, action: PlayerAction) -> GameActionResponse:
        """
        Process player action: validate → AI narration + state → apply → save.
        """
        # 1. Load state
        state_data = await self.state_manager.get_state(session_id)
        gs = GameStateManager()
        gs.load_snapshot(state_data)

        if gs.get("game_meta.game_phase") == "ending":
            raise ValueError("Game has ended")

        snapshot = gs.get_snapshot()
        game_state_pydantic = StateConverter.snapshot_to_game_state(snapshot, session_id)

        # 2. Validate action
        validation_result = await self.rules_engine.validate_action(game_state_pydantic, action)
        if not validation_result.valid:
            raise ValueError(validation_result.error or "Action invalid")

        # 3. Invoke Gemini for narration + structured response
        prompt = build_narrator_prompt(
            gs.state,
            action.action_text,
            action_id=action.action_id,
            context={"turn_history": gs.turn_history},
        )
        try:
            ai_resp = await self.gemini_client.generate_structured(
                prompt=prompt,
                response_model=AIGameActionResponse,
                model="pro",
                system_instruction=get_narrator_system_instruction(),
            )
        except GeminiAPIError as exc:
            if _is_quota_error(exc):
                logger.warning(
                    "Gemini Pro quota exceeded; retrying with Flash "
                    f"(session_id={session_id}, action_id={action.action_id}, "
                    f"action_type={action.action_type})"
                )
                try:
                    ai_resp = await self.gemini_client.generate_structured(
                        prompt=prompt,
                        response_model=AIGameActionResponse,
                        model="flash",
                        system_instruction=get_narrator_system_instruction(),
                    )
                except Exception as flash_exc:
                    logger.exception(
                        "Gemini Flash generation failed after Pro quota error; "
                        "using quota fallback response "
                        f"(session_id={session_id}, action_id={action.action_id}, "
                        f"action_type={action.action_type})",
                        exc_info=flash_exc,
                    )
                    ai_resp = _build_quota_fallback(action)
            else:
                logger.exception(
                    "Gemini API error; using fallback response "
                    f"(session_id={session_id}, action_id={action.action_id}, "
                    f"action_type={action.action_type})",
                    exc_info=exc,
                )
                ai_resp = _build_generic_fallback(action)
        except Exception as exc:
            logger.exception(
                "Gemini generation failed; using fallback response "
                f"(session_id={session_id}, action_id={action.action_id}, "
                f"action_type={action.action_type})",
                exc_info=exc,
            )
            ai_resp = _build_generic_fallback(action)

        # 3.5. Validate and auto-correct AI output to prevent AI from exceeding its authority
        ai_resp = self._validate_and_correct_ai_output(ai_resp, game_state_pydantic)

        # 4. Apply resource_changes
        for c in (ai_resp.resource_changes or []):
            path = f"resources.{c.resource_name}"
            gs.modify(path, c.change_amount, validate=False)

        # 5. Apply state_changes
        for sc in (ai_resp.state_changes or []):
            path = _entity_path(
                getattr(sc.entity_type, "value", str(sc.entity_type)),
                sc.entity_id,
                sc.field,
            )
            if path:
                val = _parse_value(sc.new_value)
                gs.set(path, val, validate=False)

        # 5.4. Check quest completion
        from app.utils.npc_quest_manager import NPCQuestManager
        from app.models.npc_quest import NPCQuest
        # Note: We'd need to store quests in game state to check completion
        # For now, quest completion is checked when player actions match quest objectives
        
        # 5.5. Apply NPC reactions and update relationships
        for reaction in (ai_resp.npc_reactions or []):
            npc_id = reaction.npc_id
            if npc_id in game_state_pydantic.npcs:
                npc = game_state_pydantic.npcs[npc_id]
                
                # Update trust level if disposition_change is provided
                if reaction.disposition_change is not None:
                    # Ensure relationship exists
                    if "player" not in npc.relationships:
                        from app.models.npc import NPCRelationship
                        npc.relationships["player"] = NPCRelationship(
                            target_npc_id="player",
                            trust_level=0,
                            relationship_history=[]
                        )
                    
                    rel = npc.relationships["player"]
                    old_trust = rel.trust_level
                    new_trust = old_trust + reaction.disposition_change
                    new_trust = max(-100, min(100, new_trust))
                    rel.trust_level = new_trust
                    
                    # Add to history if significant change
                    if abs(reaction.disposition_change) >= 5:
                        rel.relationship_history.append(
                            f"Trust changed by {reaction.disposition_change} due to player action"
                        )
                        # Keep history limited
                        if len(rel.relationship_history) > 10:
                            rel.relationship_history = rel.relationship_history[-10:]
                    
                    # Update in GameStateManager
                    gs.set(f"npcs.{npc_id}.relationships.player.trust_level", new_trust, validate=False)
                    if rel.relationship_history:
                        gs.set(f"npcs.{npc_id}.relationships.player.relationship_history", rel.relationship_history, validate=False)
                    
                    # Check for secret revelation after trust change
                    from app.utils.npc_secret_manager import NPCSecretManager
                    context = {
                        "action_type": action.action_id,
                        "trust_level_changed": True,
                        "old_trust": old_trust,
                        "new_trust": new_trust
                    }
                    revealed_secrets = NPCSecretManager.check_and_reveal_secrets(
                        npc, game_state_pydantic, context
                    )
                    if revealed_secrets:
                        # Update secret known_by_player flags in GameStateManager
                        for secret in revealed_secrets:
                            secret_idx = next(
                                (i for i, s in enumerate(npc.secrets) if s.id == secret.id),
                                None
                            )
                            if secret_idx is not None:
                                gs.set(f"npcs.{npc_id}.secrets.{secret_idx}.known_by_player", True, validate=False)
                        
                        # Update player's discovered_secrets
                        NPCSecretManager.update_player_discovered_secrets(
                            game_state_pydantic, revealed_secrets, npc_id
                        )
                        # Update in GameStateManager
                        gs.set("player.discovered_secrets", game_state_pydantic.player.discovered_secrets, validate=False)
                
                # Update current_activity if provided
                if reaction.new_activity:
                    npc.current_activity = reaction.new_activity
                    gs.set(f"npcs.{npc_id}.current_activity", reaction.new_activity, validate=False)
                
                # Update breakdown state if stress changed
                if npc.stress_level:
                    npc.update_breakdown_state()
                    gs.set(f"npcs.{npc_id}.is_in_breakdown", npc.is_in_breakdown, validate=False)

        # 6. Get action definition to determine time_cost
        time_cost = 1  # Default to 1 turn
        if self.game_data_loader:
            try:
                actions = self.game_data_loader.load_player_actions()
                action_def = actions.get(action.action_id)
                if action_def and action_def.requirements:
                    time_cost = action_def.requirements.time_cost or 1
            except Exception as e:
                logger.warning(f"[GameLoop] Failed to load action definition for {action.action_id}: {e}, using default time_cost=1")

        # 7. Execute turn end logic based on time_cost
        # Each turn: resource decay + NPC actions + increment turn
        for turn_iteration in range(time_cost):
            # Execute turn end logic (resource decay, NPC actions, etc.)
            await self._execute_turn_end_logic(gs, session_id)
            
            # Increment turn after each iteration
            gs.increment_turn()
            
            # Check for ending after each turn
            trig, eid = self._check_ending(gs)
            if trig:
                gs.set("game_meta.game_phase", "ending", validate=False)
                gs.set("game_meta.ending_triggered", eid, validate=False)
                break  # Stop processing remaining turns if game ended

        # 8. Ending: if AI says so or we detect hard conditions
        trigger = bool(ai_resp.trigger_ending and ai_resp.ending_id)
        ending_id = ai_resp.ending_id
        if not trigger:
            trig, eid = self._check_ending(gs)
            if trig:
                trigger, ending_id = True, eid
        if trigger:
            gs.set("game_meta.game_phase", "ending", validate=False)
            gs.set("game_meta.ending_triggered", ending_id, validate=False)

        # 8. Save
        final = gs.get_snapshot()
        await self.state_manager.update_state(session_id, final)

        # 9. Return (override trigger/ending_id if we detected from _check_ending)
        resp = _ai_to_model(ai_resp)
        if trigger:
            resp.trigger_ending = True
            resp.ending_id = ending_id
        return resp

    async def _execute_turn_end_logic(self, gs: GameStateManager, session_id: str) -> Dict[str, Any]:
        """
        Execute turn end logic: resource decay, NPC actions, etc.
        This is called after each player action to ensure every action triggers a full turn end cycle.
        Note: Does NOT increment turn or save state (caller handles that).
        
        Returns:
            Dict with npc_actions_taken, critical_alerts, and other turn end information
        """
        # Apply resource decay using the decay rule (reads from state_variables.json)
        game_state_pydantic = StateConverter.snapshot_to_game_state(gs.get_snapshot(), session_id)
        _, decay_changes = self.decay_rule.apply_decay(game_state_pydantic)

        # Apply decay changes to GameStateManager
        for resource_name, change_info in decay_changes.items():
            path = f"resources.{resource_name}"
            cur = gs.get(path)
            if isinstance(cur, (int, float)):
                gs.set(path, change_info["new"], validate=False)
            elif isinstance(cur, dict) and "current" in cur:
                gs.set(f"{path}.current", change_info["new"], validate=False)

        # Check for critical resources
        critical_result = self.critical_rule.validate(game_state_pydantic)
        critical_alerts = critical_result.metadata.get("warnings", []) if critical_result.metadata else []

        # Execute NPC actions
        npc_actions_taken = []
        try:
            # Convert to GameState for NPCScheduler
            snapshot_before_npcs = gs.get_snapshot()
            game_state_pydantic = StateConverter.snapshot_to_game_state(snapshot_before_npcs, session_id)
            
            # Update NPC goals dynamically
            from app.utils.npc_goals_manager import NPCGoalsManager
            for npc in game_state_pydantic.npcs.values():
                if npc.alive:
                    NPCGoalsManager.update_npc_goals(npc, game_state_pydantic)
                    # Update goals in GameStateManager
                    gs.set(f"npcs.{npc.id}.goals", npc.goals, validate=False)
            
            # Apply automatic stress increase
            from app.utils.npc_stress_manager import NPCStressManager
            for npc in game_state_pydantic.npcs.values():
                if npc.alive:
                    stress_result = NPCStressManager.apply_stress_increase(npc, game_state_pydantic)
                    # Update stress in GameStateManager
                    gs.set(f"npcs.{npc.id}.stress_level", npc.stress_level, validate=False)
                    # Update breakdown state
                    gs.set(f"npcs.{npc.id}.is_in_breakdown", npc.is_in_breakdown, validate=False)
            
            # Update NPC relationships dynamically
            from app.utils.npc_relationship_dynamics import NPCRelationshipDynamics
            relationship_changes = NPCRelationshipDynamics.update_relationships_from_interactions(game_state_pydantic)
            # Update relationships in GameStateManager
            for change in relationship_changes:
                npc1_id = change["npc1_id"]
                npc2_id = change["npc2_id"]
                rel = game_state_pydantic.npcs[npc1_id].relationships.get(npc2_id)
                if rel:
                    gs.set(f"npcs.{npc1_id}.relationships.{npc2_id}.trust_level", rel.trust_level, validate=False)
                    gs.set(f"npcs.{npc1_id}.relationships.{npc2_id}.relationship_history", rel.relationship_history, validate=False)
            
            # Check for NPC quests
            from app.utils.npc_quest_manager import NPCQuestManager
            for npc in game_state_pydantic.npcs.values():
                if npc.alive and not npc.is_in_breakdown:
                    quest = NPCQuestManager.generate_quest(npc, game_state_pydantic)
                    if quest:
                        # Add quest to player's active quests
                        if quest.quest_id not in game_state_pydantic.player.active_quests:
                            game_state_pydantic.player.active_quests.append(quest.quest_id)
                            gs.set("player.active_quests", game_state_pydantic.player.active_quests, validate=False)
                            logger.info(f"[GameLoop] NPC {npc.name} gave quest: {quest.title}")
            
            # Check for mutiny risk
            from app.utils.npc_mutiny_manager import NPCMutinyManager
            for npc in game_state_pydantic.npcs.values():
                if npc.alive:
                    mutiny_check = NPCMutinyManager.check_mutiny_risk(npc, game_state_pydantic)
                    if mutiny_check["will_mutiny"]:
                        mutiny_result = NPCMutinyManager.trigger_mutiny(npc, game_state_pydantic)
                        # Update trust in GameStateManager
                        if "player" in npc.relationships:
                            rel = npc.relationships["player"]
                            gs.set(f"npcs.{npc.id}.relationships.player.trust_level", rel.trust_level, validate=False)
                            gs.set(f"npcs.{npc.id}.relationships.player.relationship_history", rel.relationship_history, validate=False)
                        # Update morale
                        if hasattr(game_state_pydantic.world, 'crew_morale'):
                            gs.set("world.crew_morale", game_state_pydantic.world.crew_morale, validate=False)
            
            # Check for sacrifice opportunities
            from app.utils.npc_sacrifice_manager import NPCSacrificeManager
            for npc in game_state_pydantic.npcs.values():
                if npc.alive:
                    sacrifice_opp = NPCSacrificeManager.check_sacrifice_opportunity(npc, game_state_pydantic)
                    if sacrifice_opp and sacrifice_opp["willingness"] >= 50:
                        # NPC decides to sacrifice (probability based on willingness)
                        if random.random() < (sacrifice_opp["willingness"] / 100.0):
                            sacrifice_result = NPCSacrificeManager.execute_sacrifice(
                                npc, game_state_pydantic, sacrifice_opp["opportunity"]["type"]
                            )
                            # Update NPC alive status
                            gs.set(f"npcs.{npc.id}.alive", False, validate=False)
                            gs.set(f"npcs.{npc.id}.health", 0, validate=False)
                            # Update resources if applicable
                            if "benefits" in sacrifice_result:
                                benefits = sacrifice_result["benefits"]
                                if "oxygen_restored" in benefits:
                                    current_oxygen = gs.get("world.resources.oxygen_level.current") or gs.get("world.resources.oxygen_level") or 0
                                    gs.set("world.resources.oxygen_level.current", 
                                           min(100, current_oxygen + benefits["oxygen_restored"]), 
                                           validate=False)
                                if "reactor_stabilized" in benefits and benefits["reactor_stabilized"]:
                                    current_reactor = gs.get("world.resources.reactor_level.current") or gs.get("world.resources.reactor_level") or 0
                                    gs.set("world.resources.reactor_level.current", 
                                           min(100, current_reactor + 50), 
                                           validate=False)
                            # Update morale
                            if "benefits" in sacrifice_result and "morale_boost" in sacrifice_result["benefits"]:
                                gs.set("world.crew_morale", game_state_pydantic.world.crew_morale, validate=False)
            
            # Check environmental damage
            from app.utils.npc_health_manager import NPCHealthManager
            for npc in game_state_pydantic.npcs.values():
                if npc.alive:
                    damage_result = NPCHealthManager.check_environmental_damage(npc, game_state_pydantic)
                    if damage_result:
                        # Update health in GameStateManager
                        gs.set(f"npcs.{npc.id}.health", npc.health, validate=False)
                        if damage_result.get("died"):
                            gs.set(f"npcs.{npc.id}.alive", False, validate=False)
                            # Handle death
                            from app.utils.npc_death_handler import NPCDeathHandler
                            death_result = NPCDeathHandler.handle_npc_death(
                                npc, game_state_pydantic, damage_result.get("reason", "environmental_damage")
                            )
                            # Update morale/panic
                            if "morale_impact" in death_result:
                                gs.set("world.crew_morale", game_state_pydantic.world.crew_morale, validate=False)
                            if "panic_impact" in death_result:
                                gs.set("world.panic_level", game_state_pydantic.world.panic_level, validate=False)
                            # Update stress for other NPCs
                            for other_npc_id, stress_delta in death_result.get("stress_impact", {}).items():
                                current_stress = gs.get(f"npcs.{other_npc_id}.stress_level") or 0
                                gs.set(f"npcs.{other_npc_id}.stress_level", min(100, current_stress + stress_delta), validate=False)
            
            # Execute all NPC turns
            npc_results = await self.npc_scheduler.execute_all_npc_turns(game_state_pydantic)
            
            # Apply NPC action state changes to GameStateManager
            for result in npc_results:
                if result.get("success") and result.get("state_changes"):
                    npc_id = result["npc_id"]
                    changes = result["state_changes"]
                    
                    # Apply changes to NPC state
                    if "current_activity" in changes:
                        gs.set(f"npcs.{npc_id}.current_activity", changes["current_activity"], validate=False)
                    if "stress_level" in changes:
                        gs.set(f"npcs.{npc_id}.stress_level", changes["stress_level"], validate=False)
                    if "location" in changes:
                        gs.set(f"npcs.{npc_id}.location", changes["location"], validate=False)
                    
                    # Format action for response
                    npc_actions_taken.append({
                        "npc_id": npc_id,
                        "npc_name": result.get("npc_name", "Unknown"),
                        "action_type": result.get("action_type", "unknown"),
                        "description": result.get("description", ""),
                    })
        except Exception as e:
            logger.error(f"[GameLoop] Error executing turn end logic: {e}")
            import traceback
            traceback.print_exc()
        
        return {
            "npc_actions_taken": npc_actions_taken,
            "critical_alerts": critical_alerts,
        }

    def _check_ending(self, gs: GameStateManager) -> Tuple[bool, Optional[str]]:
        """Simple ending checks: oxygen, player health, turn limit."""
        ox = gs.get("resources.oxygen_level", 100)
        if isinstance(ox, dict):
            ox = ox.get("current", 100)
        if isinstance(ox, (int, float)) and ox <= 0:
            return True, "ending_oxygen"
        health = gs.get("player.health", 100)
        if isinstance(health, (int, float)) and health <= 0:
            return True, "ending_death"
        turn = gs.get("game_meta.current_turn", 0) or 0
        if turn >= 84:  # 7 days * 12 turns
            return True, "ending_rescue"
        return False, None

    def _validate_and_correct_ai_output(
        self,
        ai_resp: AIGameActionResponse,
        game_state,
    ) -> AIGameActionResponse:
        """
        Validate AI output and auto-correct if necessary.

        This is the key defense against AI "exceeding its authority":
        - Prevents AI from referencing non-existent NPCs/locations/items
        - Prevents unauthorized NPC deaths
        - Prevents modification of readonly fields
        - Prevents early ending triggers
        - Clamps resource changes to reasonable ranges

        Args:
            ai_resp: AI-generated response
            game_state: Current game state (Pydantic model)

        Returns:
            Validated and potentially corrected AI response
        """
        # Build validation context from current game state
        context = GameContext(
            valid_npcs=set(game_state.npcs.keys()),
            valid_locations=set(getattr(game_state.world, 'locations', {}).keys()) or {
                "cryo_bay", "command_bridge", "engineering", "reactor_room",
                "med_bay", "crew_quarters", "mess_hall", "cargo_bay", "observation_deck"
            },
            valid_items=set(game_state.player.inventory or []),
            discovered_secrets=set(game_state.player.discovered_secrets or []),
            player_inventory=set(game_state.player.inventory or []),
            player_location=game_state.player.location,
            current_day=getattr(game_state.world, 'day', 1) or 1,
            npc_alive_status={
                npc_id: npc.alive
                for npc_id, npc in game_state.npcs.items()
            },
            allow_death=self._should_allow_death(game_state),
            resource_levels=self._get_resource_levels(game_state),
        )

        # Validate AI output
        validation_result = self.ai_validator.validate(ai_resp, context)

        # Log validation errors if any
        if not validation_result.valid:
            for error in validation_result.errors:
                logger.warning(
                    f"[AI Validation Error] {error.code}: {error.message} "
                    f"(field: {error.field}, value: {error.value})"
                )

        # Log warnings
        for warning in validation_result.warnings:
            logger.info(
                f"[AI Validation Warning] {warning.code}: {warning.message}"
            )

        # Auto-correct the response if there are errors or warnings
        if validation_result.errors or validation_result.warnings:
            ai_resp = self.ai_validator.auto_correct(ai_resp, context, validation_result)
            logger.info("[AI Output] Auto-corrected AI response to ensure game integrity")

        return ai_resp

    def _should_allow_death(self, game_state) -> bool:
        """
        Check if NPC death should be allowed in current game state.

        Deaths are allowed when:
        - Resources are critical (crew may die from environmental causes)
        - It's late in the game (day 5+)
        - Special story events are active
        """
        # Check if resources are critically low
        resources = game_state.world.resources
        oxygen = getattr(resources, 'oxygen_level', None)
        if oxygen:
            current = oxygen.current if hasattr(oxygen, 'current') else oxygen
            if isinstance(current, (int, float)) and current <= 10:
                return True

        # Allow death in late game
        current_day = getattr(game_state.world, 'day', 1) or 1
        if current_day >= 5:
            return True

        # Check for story events that enable death
        player_flags = game_state.player.flags or {}
        if player_flags.get("crisis_active") or player_flags.get("mutiny_in_progress"):
            return True

        return False

    def _get_resource_levels(self, game_state) -> dict:
        """Extract current resource levels from game state."""
        resources = game_state.world.resources
        levels = {}

        resource_names = [
            "oxygen_level", "fuel_reserves", "power_level",
            "food_water", "medical_supplies", "repair_materials"
        ]

        for name in resource_names:
            resource = getattr(resources, name, None)
            if resource is not None:
                if hasattr(resource, 'current'):
                    levels[name] = resource.current
                elif isinstance(resource, (int, float)):
                    levels[name] = resource

        return levels

    async def process_action_stream(
        self, session_id: str, action: PlayerAction
    ) -> AsyncGenerator[str, None]:
        """
        Process action and yield narration in chunks, then a final 'complete' payload.
        For now, uses full process_action and chunks the narration.
        """
        resp = await self.process_action(session_id, action)
        # Chunk by sentence for faux streaming
        import re
        parts = re.split(r'(?<=[.!?])\s+', resp.narration) or [resp.narration]
        for p in parts:
            if p:
                yield p + " "
        # Final "complete" marker: caller can use a different protocol (e.g. SSE) to send {type:"complete", response}
        yield "\n"

    async def get_state(self, session_id: str):
        """Get current game state as GameState (Pydantic)."""
        state_data = await self.state_manager.get_state(session_id)
        return StateConverter.snapshot_to_game_state(state_data, session_id)

    async def advance_turn(self, session_id: str) -> Dict[str, Any]:
        """
        Advance turn: resource decay, NPC actions, increment, save.
        Returns a dict compatible with TurnEndResponse.
        This is called when player clicks "End Turn" button - advances exactly 1 turn.
        """
        state_data = await self.state_manager.get_state(session_id)
        gs = GameStateManager()
        gs.load_snapshot(state_data)

        if gs.get("game_meta.game_phase") == "ending":
            raise ValueError("Game has ended")

        # Execute turn end logic (resource decay, NPC actions, etc.)
        turn_end_info = await self._execute_turn_end_logic(gs, session_id)
        npc_actions_taken = turn_end_info.get("npc_actions_taken", [])
        critical_alerts = turn_end_info.get("critical_alerts", [])

        # Increment turn (End Turn button advances exactly 1 turn)
        gs.increment_turn()

        # Ending check
        trig, eid = self._check_ending(gs)
        if trig:
            gs.set("game_meta.game_phase", "ending", validate=False)
            gs.set("game_meta.ending_triggered", eid, validate=False)

        snapshot = gs.get_snapshot()
        await self.state_manager.update_state(session_id, snapshot)

        # Build narration
        narration_parts = ["Time passes. The ship's systems continue their steady decline."]
        if npc_actions_taken:
            action_descriptions = [f"{action['npc_name']} {action['description']}" for action in npc_actions_taken[:3]]
            narration_parts.append("Around the ship: " + "; ".join(action_descriptions))
        
        return {
            "events_occurred": [],
            "npc_actions_taken": npc_actions_taken,
            "state_summary": {
                "resources_decayed": True,
                "turn_advanced": True,
                "npc_actions": len(npc_actions_taken),
            },
            "narration": " ".join(narration_parts),
            "critical_alerts": critical_alerts,
            "turn_number": gs.get("game_meta.current_turn"),
        }
