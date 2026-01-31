"""NPC breakdown recovery system - therapy, counseling, and recovery from breakdown."""
from typing import Dict, Any, Optional
from app.models.npc import NPCState
from app.models.game_state import GameState
from app.utils.logger import get_logger
import random

logger = get_logger(__name__)


class NPCRecoveryManager:
    """Manages NPC recovery from breakdown state."""

    @staticmethod
    def provide_therapy(
        therapist: NPCState,
        patient: NPCState,
        game_state: GameState,
        therapy_type: str = "counseling"
    ) -> Dict[str, Any]:
        """
        Provide therapy/counseling to help NPC recover from breakdown.

        Args:
            therapist: NPC providing therapy (should be Medical Officer or similar)
            patient: NPC receiving therapy
            game_state: Current GameState
            therapy_type: Type of therapy ("counseling", "medical", "rest", "forced_rest")

        Returns:
            dict: Therapy result
        """
        if not therapist.alive or not patient.alive:
            return {
                "success": False,
                "reason": "One or both NPCs are not available"
            }
        
        if not patient.is_in_breakdown:
            return {
                "success": False,
                "reason": f"{patient.name} is not in breakdown state"
            }
        
        # Check if therapist is qualified
        if therapy_type in ["counseling", "medical"]:
            if "medical" not in therapist.role.lower() and "doctor" not in therapist.role.lower():
                return {
                    "success": False,
                    "reason": f"{therapist.name} is not qualified to provide {therapy_type}"
                }
        
        # Calculate recovery chance
        recovery_chance = NPCRecoveryManager._calculate_recovery_chance(
            therapist, patient, therapy_type, game_state
        )
        
        # Apply therapy
        stress_reduction = NPCRecoveryManager._calculate_stress_reduction(
            therapist, patient, therapy_type
        )
        
        old_stress = patient.stress_level
        patient.stress_level = max(0, patient.stress_level - stress_reduction)
        
        # Check if recovered from breakdown
        recovered = False
        if patient.is_in_breakdown:
            patient.update_breakdown_state()
            if not patient.is_in_breakdown:
                recovered = True
                logger.info(f"[NPCRecoveryManager] {patient.name} recovered from breakdown!")
        
        # Update relationship between therapist and patient
        if patient.id not in therapist.relationships:
            from app.models.npc import NPCRelationship
            therapist.relationships[patient.id] = NPCRelationship(target_npc_id=patient.id)
        
        rel = therapist.relationships[patient.id]
        rel.trust_level = min(100, rel.trust_level + 5)
        rel.relationship_history.append(f"{therapist.name} provided {therapy_type} therapy")
        if len(rel.relationship_history) > 10:
            rel.relationship_history = rel.relationship_history[-10:]
        
        # Boost morale slightly if successful
        morale_boost = 0
        if recovered and hasattr(game_state.world, 'crew_morale'):
            morale_boost = 3
            game_state.world.crew_morale = min(100, game_state.world.crew_morale + morale_boost)
        
        return {
            "success": True,
            "therapist_id": therapist.id,
            "therapist_name": therapist.name,
            "patient_id": patient.id,
            "patient_name": patient.name,
            "therapy_type": therapy_type,
            "stress_reduction": stress_reduction,
            "old_stress": old_stress,
            "new_stress": patient.stress_level,
            "recovered_from_breakdown": recovered,
            "morale_boost": morale_boost,
            "message": f"{therapist.name} provided {therapy_type} to {patient.name}. Stress reduced by {stress_reduction}."
        }

    @staticmethod
    def player_provide_counseling(
        patient: NPCState,
        game_state: GameState,
        counseling_approach: str = "supportive"
    ) -> Dict[str, Any]:
        """
        Player provides counseling to NPC in breakdown.

        Args:
            patient: NPC receiving counseling
            game_state: Current GameState
            counseling_approach: Approach ("supportive", "directive", "empathetic")

        Returns:
            dict: Counseling result
        """
        if not patient.alive:
            return {
                "success": False,
                "reason": f"{patient.name} is not available"
            }
        
        if not patient.is_in_breakdown:
            return {
                "success": False,
                "reason": f"{patient.name} is not in breakdown state"
            }
        
        # Get player trust
        player_trust = 0
        if "player" in patient.relationships:
            player_trust = patient.relationships["player"].trust_level
        
        # Calculate effectiveness based on trust and approach
        base_reduction = 10
        if counseling_approach == "empathetic":
            base_reduction = 15
        elif counseling_approach == "directive":
            base_reduction = 8
        
        # Trust modifier
        if player_trust >= 50:
            base_reduction = int(base_reduction * 1.3)
        elif player_trust < 0:
            base_reduction = int(base_reduction * 0.7)
        
        # Apply stress reduction
        old_stress = patient.stress_level
        patient.stress_level = max(0, patient.stress_level - base_reduction)
        
        # Check if recovered
        recovered = False
        if patient.is_in_breakdown:
            patient.update_breakdown_state()
            if not patient.is_in_breakdown:
                recovered = True
        
        # Update player relationship
        if "player" in patient.relationships:
            rel = patient.relationships["player"]
            trust_increase = 10 if recovered else 5
            rel.trust_level = min(100, rel.trust_level + trust_increase)
            rel.relationship_history.append(f"Player provided {counseling_approach} counseling")
            if len(rel.relationship_history) > 10:
                rel.relationship_history = rel.relationship_history[-10:]
        
        # Boost morale
        morale_boost = 0
        if recovered and hasattr(game_state.world, 'crew_morale'):
            morale_boost = 5
            game_state.world.crew_morale = min(100, game_state.world.crew_morale + morale_boost)
        
        logger.info(f"[NPCRecoveryManager] Player provided counseling to {patient.name}. Recovered: {recovered}")
        
        return {
            "success": True,
            "patient_id": patient.id,
            "patient_name": patient.name,
            "counseling_approach": counseling_approach,
            "stress_reduction": base_reduction,
            "old_stress": old_stress,
            "new_stress": patient.stress_level,
            "recovered_from_breakdown": recovered,
            "trust_increase": trust_increase if "player" in patient.relationships else 0,
            "morale_boost": morale_boost,
            "message": f"Provided {counseling_approach} counseling to {patient.name}. Stress reduced by {base_reduction}."
        }

    @staticmethod
    def force_rest(
        npc: NPCState,
        game_state: GameState,
        enforcer: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Force NPC to rest (for breakdown recovery).

        Args:
            npc: NPC to force rest
            game_state: Current GameState
            enforcer: Who is enforcing rest ("player" or NPC ID)

        Returns:
            dict: Rest result
        """
        if not npc.alive:
            return {
                "success": False,
                "reason": f"{npc.name} is not available"
            }
        
        # Force rest - significant stress reduction
        old_stress = npc.stress_level
        stress_reduction = 20  # Significant reduction
        npc.stress_level = max(0, npc.stress_level - stress_reduction)
        
        # Update breakdown state
        recovered = False
        if npc.is_in_breakdown:
            npc.update_breakdown_state()
            if not npc.is_in_breakdown:
                recovered = True
        
        # Update activity
        npc.current_activity = "forced rest"
        
        # Relationship impact (may be negative if NPC resents being forced)
        if enforcer == "player" and "player" in npc.relationships:
            rel = npc.relationships["player"]
            if recovered:
                # NPC appreciates the help
                rel.trust_level = min(100, rel.trust_level + 5)
                rel.relationship_history.append("Player forced rest - helped recover from breakdown")
            else:
                # NPC may resent being forced
                if npc.personality.core_value == "independence":
                    rel.trust_level = max(-100, rel.trust_level - 3)
                    rel.relationship_history.append("Player forced rest - resented")
                else:
                    rel.trust_level = min(100, rel.trust_level + 2)
                    rel.relationship_history.append("Player forced rest")
            if len(rel.relationship_history) > 10:
                rel.relationship_history = rel.relationship_history[-10:]
        
        logger.info(f"[NPCRecoveryManager] Forced {npc.name} to rest. Recovered: {recovered}")
        
        return {
            "success": True,
            "npc_id": npc.id,
            "npc_name": npc.name,
            "stress_reduction": stress_reduction,
            "old_stress": old_stress,
            "new_stress": npc.stress_level,
            "recovered_from_breakdown": recovered,
            "message": f"Forced {npc.name} to rest. Stress reduced by {stress_reduction}."
        }

    @staticmethod
    def _calculate_recovery_chance(
        therapist: NPCState,
        patient: NPCState,
        therapy_type: str,
        game_state: GameState
    ) -> float:
        """Calculate probability of successful recovery."""
        base_chance = 0.5
        
        # Therapist qualification
        if "medical" in therapist.role.lower() or "doctor" in therapist.role.lower():
            base_chance += 0.2
        
        # Therapy type
        if therapy_type == "medical":
            base_chance += 0.1
        elif therapy_type == "counseling":
            base_chance += 0.05
        
        # Relationship between therapist and patient
        if patient.id in therapist.relationships:
            trust = therapist.relationships[patient.id].trust_level
            if trust > 50:
                base_chance += 0.1
            elif trust < 0:
                base_chance -= 0.1
        
        # Patient personality
        if hasattr(patient.personality, 'stress_response'):
            if patient.personality.stress_response == "withdraws":
                base_chance -= 0.1
            elif patient.personality.stress_response == "proactive":
                base_chance += 0.1
        
        return max(0.2, min(0.9, base_chance))

    @staticmethod
    def _calculate_stress_reduction(
        therapist: NPCState,
        patient: NPCState,
        therapy_type: str
    ) -> int:
        """Calculate stress reduction amount."""
        base_reduction = 10
        
        # Therapy type modifier
        if therapy_type == "medical":
            base_reduction = 15
        elif therapy_type == "counseling":
            base_reduction = 12
        elif therapy_type == "rest":
            base_reduction = 8
        elif therapy_type == "forced_rest":
            base_reduction = 20
        
        # Therapist skill (if medical role)
        if "medical" in therapist.role.lower() or "doctor" in therapist.role.lower():
            base_reduction = int(base_reduction * 1.2)
        
        # Random variation
        variation = random.randint(-3, 3)
        base_reduction = max(5, base_reduction + variation)
        
        return base_reduction
