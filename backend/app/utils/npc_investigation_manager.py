"""NPC investigation system - investigate NPC backgrounds and suspicious behavior."""
from typing import Dict, Any, Optional, List
from app.models.npc import NPCState
from app.models.game_state import GameState
from app.utils.logger import get_logger
import random

logger = get_logger(__name__)


class NPCInvestigationManager:
    """Manages player investigation of NPCs."""

    @staticmethod
    def investigate_npc(
        target_npc: NPCState,
        game_state: GameState,
        investigation_type: str = "background",
        investigation_method: str = "questioning"
    ) -> Dict[str, Any]:
        """
        Investigate an NPC for suspicious behavior or background.

        Args:
            target_npc: NPC being investigated
            game_state: Current GameState
            investigation_type: Type of investigation ("background", "suspicious_behavior", "hidden_agenda", "secrets")
            investigation_method: Method ("questioning", "observation", "records_check", "confrontation")

        Returns:
            dict: Investigation results
        """
        if not target_npc.alive:
            return {
                "success": False,
                "reason": f"{target_npc.name} is not available"
            }
        
        # Calculate investigation success
        success_chance = NPCInvestigationManager._calculate_investigation_success(
            target_npc, investigation_type, investigation_method, game_state
        )
        
        success = random.random() < success_chance
        
        if not success:
            # Investigation failed - may alert NPC
            alert_chance = 0.3 if investigation_method == "questioning" else 0.1
            alerted = random.random() < alert_chance
            
            if alerted and "player" in target_npc.relationships:
                rel = target_npc.relationships["player"]
                rel.trust_level = max(-100, rel.trust_level - 5)
                rel.relationship_history.append("Player investigated - felt suspicious")
                if len(rel.relationship_history) > 10:
                    rel.relationship_history = rel.relationship_history[-10:]
            
            return {
                "success": False,
                "reason": "Investigation did not reveal useful information",
                "alerted_npc": alerted,
                "trust_change": -5 if alerted else 0
            }
        
        # Investigation successful - gather information
        findings = []
        
        # Check for hidden agenda
        if investigation_type in ["hidden_agenda", "background"] and target_npc.hidden_agenda:
            findings.append({
                "type": "hidden_agenda",
                "description": f"{target_npc.name} has a hidden agenda: {target_npc.hidden_agenda}",
                "confidence": "high" if investigation_method == "records_check" else "medium"
            })
        
        # Check for secrets
        if investigation_type in ["secrets", "background"]:
            unrevealed_secrets = [s for s in target_npc.secrets if not s.known_by_player]
            if unrevealed_secrets:
                # Reveal one secret (with chance)
                if random.random() < 0.5:
                    secret = random.choice(unrevealed_secrets)
                    findings.append({
                        "type": "secret",
                        "description": f"Discovered secret: {secret.content}",
                        "confidence": "medium"
                    })
        
        # Check for suspicious behavior indicators
        suspicious_indicators = []
        
        if target_npc.stress_level > 80:
            suspicious_indicators.append("extremely high stress levels")
        if target_npc.is_in_breakdown:
            suspicious_indicators.append("recent breakdown behavior")
        if target_npc.hidden_agenda_conflicts_with_player:
            suspicious_indicators.append("agenda conflicts with player goals")
        
        # Check relationships for suspicious patterns
        negative_relationships = sum(1 for rel in target_npc.relationships.values() if rel.trust_level < -30)
        if negative_relationships > 2:
            suspicious_indicators.append("multiple negative relationships with crew")
        
        if suspicious_indicators:
            findings.append({
                "type": "suspicious_behavior",
                "description": f"Suspicious indicators: {', '.join(suspicious_indicators)}",
                "confidence": "medium"
            })
        
        # Background information
        if investigation_type == "background":
            background_info = {
                "type": "background",
                "description": f"{target_npc.name} is a {target_npc.role}. Personality: {target_npc.personality.core_value if hasattr(target_npc.personality, 'core_value') else 'unknown'}",
                "confidence": "high"
            }
            findings.append(background_info)
        
        # Relationship impact
        trust_change = 0
        if "player" in target_npc.relationships:
            rel = target_npc.relationships["player"]
            if investigation_method == "confrontation":
                trust_change = -10
            elif investigation_method == "questioning":
                trust_change = -3
            elif investigation_method == "observation":
                trust_change = 0  # No impact if not detected
            else:
                trust_change = -2
            
            rel.trust_level = max(-100, rel.trust_level + trust_change)
            rel.relationship_history.append(f"Player investigated ({investigation_type})")
            if len(rel.relationship_history) > 10:
                rel.relationship_history = rel.relationship_history[-10:]
        
        logger.info(f"[NPCInvestigationManager] Investigation of {target_npc.name} revealed {len(findings)} findings")
        
        return {
            "success": True,
            "target_npc_id": target_npc.id,
            "target_npc_name": target_npc.name,
            "investigation_type": investigation_type,
            "investigation_method": investigation_method,
            "findings": findings,
            "trust_change": trust_change,
            "message": f"Investigation of {target_npc.name} revealed {len(findings)} findings"
        }

    @staticmethod
    def check_suspicious_behavior(
        game_state: GameState
    ) -> List[Dict[str, Any]]:
        """
        Check all NPCs for suspicious behavior patterns.

        Args:
            game_state: Current GameState

        Returns:
            List of suspicious NPCs with indicators
        """
        suspicious_npcs = []
        
        for npc in game_state.npcs.values():
            if not npc.alive:
                continue
            
            suspicious_score = 0
            indicators = []
            
            # High stress
            if npc.stress_level > 80:
                suspicious_score += 2
                indicators.append("extremely high stress")
            
            # Breakdown state
            if npc.is_in_breakdown:
                suspicious_score += 3
                indicators.append("breakdown behavior")
            
            # Hidden agenda conflicts
            if npc.hidden_agenda_conflicts_with_player:
                suspicious_score += 4
                indicators.append("conflicting agenda")
            
            # Many negative relationships
            negative_rels = sum(1 for rel in npc.relationships.values() if rel.trust_level < -30)
            if negative_rels > 2:
                suspicious_score += 2
                indicators.append("multiple negative relationships")
            
            # Low trust with player
            if "player" in npc.relationships:
                player_trust = npc.relationships["player"].trust_level
                if player_trust < -50:
                    suspicious_score += 3
                    indicators.append("very low trust with player")
            
            # Unusual activity
            if npc.current_activity and any(keyword in npc.current_activity.lower() for keyword in ["sabotage", "hide", "secret", "alone"]):
                suspicious_score += 2
                indicators.append("unusual activity")
            
            if suspicious_score >= 3:
                suspicious_npcs.append({
                    "npc_id": npc.id,
                    "npc_name": npc.name,
                    "suspicious_score": suspicious_score,
                    "indicators": indicators
                })
        
        return suspicious_npcs

    @staticmethod
    def _calculate_investigation_success(
        target_npc: NPCState,
        investigation_type: str,
        method: str,
        game_state: GameState
    ) -> float:
        """Calculate probability of successful investigation."""
        base_chance = 0.4
        
        # Method modifier
        if method == "records_check":
            base_chance += 0.3  # Most reliable
        elif method == "observation":
            base_chance += 0.2
        elif method == "questioning":
            base_chance += 0.1
        elif method == "confrontation":
            base_chance += 0.15  # Direct but risky
        
        # Investigation type
        if investigation_type == "background":
            base_chance += 0.2  # Easier to find
        elif investigation_type == "hidden_agenda":
            base_chance -= 0.1  # Harder to find
        
        # NPC trust with player (lower trust = easier to investigate suspicious behavior)
        if "player" in target_npc.relationships:
            player_trust = target_npc.relationships["player"].trust_level
            if player_trust < -30:
                base_chance += 0.1  # Suspicious NPCs easier to investigate
            elif player_trust > 50:
                base_chance -= 0.1  # Trusted NPCs harder to investigate
        
        # NPC stress (stressed NPCs may reveal more)
        if target_npc.stress_level > 70:
            base_chance += 0.1
        
        # NPC is in breakdown (may reveal secrets)
        if target_npc.is_in_breakdown:
            base_chance += 0.15
        
        return max(0.2, min(0.9, base_chance))
