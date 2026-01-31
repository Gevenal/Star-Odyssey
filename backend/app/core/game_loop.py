"""Game loop orchestration."""
from typing import AsyncGenerator, Dict, Any, Optional, Tuple

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

    def __init__(self, state_manager, rules_engine, gemini_client):
        """
        Initialize game loop with dependencies.

        Args:
            state_manager: SessionStateManager
            rules_engine: RulesEngine
            gemini_client: GeminiClient
        """
        self.state_manager = state_manager
        self.rules_engine = rules_engine
        self.gemini_client = gemini_client
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
        except Exception:
            # Fallback when AI fails: minimal response, still advance turn
            ai_resp = AIGameActionResponse(
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

        # 6. Increment turn
        gs.increment_turn()

        # 7. Ending: if AI says so or we detect hard conditions
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
        """
        state_data = await self.state_manager.get_state(session_id)
        gs = GameStateManager()
        gs.load_snapshot(state_data)

        if gs.get("game_meta.game_phase") == "ending":
            raise ValueError("Game has ended")

        # Simple decay: subtract fixed amounts from resources if they exist
        for name, key in [
            ("oxygen_level", 1.2),
            ("fuel_reserves", 0.8),
            ("power_level", 1.0),
            ("food_water", 0.9),
        ]:
            path = f"resources.{name}"
            cur = gs.get(path)
            if isinstance(cur, (int, float)):
                gs.modify(path, -min(key, cur), validate=False)
            elif isinstance(cur, dict) and "current" in cur:
                gs.set(f"{path}.current", max(0, (cur.get("current") or 0) - key), validate=False)

        # Execute NPC actions
        npc_actions_taken = []
        death_events = []
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
                            death_events.append(death_result)
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
            print(f"[GameLoop] Error executing NPC actions: {e}")
            import traceback
            traceback.print_exc()

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
        
        # Add death events to narration
        if death_events:
            for death_event in death_events:
                death_npc = death_event["death_event"]
                from app.utils.npc_death_handler import NPCDeathHandler
                # Get NPC for narration - reload state if needed
                snapshot_for_npc = gs.get_snapshot()
                game_state_for_npc = StateConverter.snapshot_to_game_state(snapshot_for_npc, session_id)
                npc = game_state_for_npc.npcs.get(death_npc["npc_id"])
                if npc:
                    death_narration = NPCDeathHandler.generate_death_narration(npc, death_npc["cause"])
                    narration_parts.append(death_narration)

        return {
            "events_occurred": [e["death_event"] for e in death_events] if death_events else [],
            "npc_actions_taken": npc_actions_taken,
            "state_summary": {
                "resources_decayed": True,
                "turn_advanced": True,
                "npc_actions": len(npc_actions_taken),
                "deaths": len(death_events)
            },
            "narration": " ".join(narration_parts),
            "critical_alerts": [],
            "turn_number": gs.get("game_meta.current_turn"),
        }
