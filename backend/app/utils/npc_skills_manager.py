"""NPC skills system - quantized skill levels affecting action success rates."""
from typing import Dict, Any, Optional, List
from app.models.npc import NPCState
from app.models.game_state import GameState
from app.utils.logger import get_logger
import random

logger = get_logger(__name__)


class NPCSkillsManager:
    """Manages NPC skill levels and skill-based action success."""

    # Skill categories and their associated roles
    SKILL_CATEGORIES = {
        "medical": ["Medical Officer", "Chief Medical Officer", "Doctor"],
        "engineering": ["Engineer", "Chief Engineer", "Maintenance Tech"],
        "repair": ["Engineer", "Chief Engineer", "Maintenance Tech"],
        "security": ["Security Officer", "Security"],
        "navigation": ["Pilot", "Navigation Officer"],
        "communication": ["Communications Officer"],
        "science": ["Scientist", "Research Officer"],
        "leadership": ["Captain", "Commander"],
        "cooking": ["Cook", "Morale Officer"],
        "investigation": ["Security Officer", "Scientist"],
    }

    @staticmethod
    def initialize_npc_skills(npc: NPCState) -> Dict[str, int]:
        """
        Initialize skills for an NPC based on their role.

        Args:
            npc: NPC to initialize skills for

        Returns:
            dict: Initialized skills
        """
        skills = {}
        role_lower = npc.role.lower()
        
        # Base skills from role
        for skill, roles in NPCSkillsManager.SKILL_CATEGORIES.items():
            if any(r.lower() in role_lower for r in roles):
                # Primary skill for this role - high level
                base_level = random.randint(60, 85)
                skills[skill] = base_level
            else:
                # Secondary skill - lower level
                if random.random() < 0.3:  # 30% chance to have secondary skill
                    base_level = random.randint(20, 50)
                    skills[skill] = base_level
        
        # Add some general skills
        if "leadership" not in skills and ("captain" in role_lower or "commander" in role_lower):
            skills["leadership"] = random.randint(70, 90)
        
        # Personality affects skill levels
        if hasattr(npc, 'personality') and npc.personality:
            if hasattr(npc.personality, 'decision_making'):
                if npc.personality.decision_making == "data-driven":
                    # Better at technical skills
                    for skill in ["engineering", "science", "investigation"]:
                        if skill in skills:
                            skills[skill] = min(100, skills[skill] + 5)
                elif npc.personality.decision_making == "intuitive":
                    # Better at social/leadership skills
                    for skill in ["leadership", "communication"]:
                        if skill in skills:
                            skills[skill] = min(100, skills[skill] + 5)
        
        npc_name = getattr(npc, 'name', getattr(npc, 'role', 'Unknown'))
        logger.debug(f"[NPCSkillsManager] Initialized skills for {npc_name}: {skills}")
        return skills

    @staticmethod
    def get_skill_level(npc: NPCState, skill_name: str) -> int:
        """
        Get NPC's skill level for a specific skill.

        Args:
            npc: NPC to check
            skill_name: Name of skill

        Returns:
            int: Skill level (0-100), 0 if skill doesn't exist
        """
        return npc.skills.get(skill_name, 0)

    @staticmethod
    def calculate_action_success(
        npc: NPCState,
        action_type: str,
        required_skill: Optional[str] = None,
        difficulty: int = 50
    ) -> Dict[str, Any]:
        """
        Calculate success chance for an NPC action based on skills.

        Args:
            npc: NPC performing action
            action_type: Type of action ("repair", "medical", "investigation", etc.)
            required_skill: Specific skill required (if None, inferred from action_type)
            difficulty: Difficulty level (0-100, higher = harder)

        Returns:
            dict: Success calculation result
        """
        # Infer skill from action type if not provided
        if not required_skill:
            skill_mapping = {
                "repair": "repair",
                "medical": "medical",
                "heal": "medical",
                "investigation": "investigation",
                "security": "security",
                "navigation": "navigation",
                "communication": "communication",
                "science": "science",
                "engineering": "engineering",
                "leadership": "leadership",
            }
            required_skill = skill_mapping.get(action_type.lower(), "general")
        
        # Get skill level
        skill_level = NPCSkillsManager.get_skill_level(npc, required_skill)
        
        # If skill doesn't exist, use base level (30) for general actions
        if skill_level == 0 and required_skill != "general":
            # Check if NPC has related skills
            related_skills = NPCSkillsManager._get_related_skills(required_skill)
            for related in related_skills:
                if related in npc.skills:
                    skill_level = int(npc.skills[related] * 0.7)  # 70% of related skill
                    break
            
            if skill_level == 0:
                skill_level = 30  # Base level for unskilled actions
        
        # Calculate success chance
        # Formula: skill_level - difficulty + modifiers
        base_success = skill_level - difficulty
        
        # Stress modifier (high stress reduces effectiveness)
        stress_penalty = int((npc.stress_level / 100.0) * 20)  # Up to -20
        base_success -= stress_penalty
        
        # Health modifier (low health reduces effectiveness)
        health_penalty = int(((100 - npc.health) / 100.0) * 15)  # Up to -15
        base_success -= health_penalty
        
        # Breakdown modifier
        if npc.is_in_breakdown:
            base_success -= 30  # Significant penalty
        
        # Clamp success chance
        success_chance = max(5, min(95, base_success))
        
        # Determine if action succeeds
        success = random.randint(1, 100) <= success_chance
        
        logger.debug(
            f"[NPCSkillsManager] {npc.name} attempting {action_type} "
            f"(skill: {required_skill}={skill_level}, difficulty={difficulty}, "
            f"success_chance={success_chance}%, success={success})"
        )
        
        return {
            "success": success,
            "skill_used": required_skill,
            "skill_level": skill_level,
            "difficulty": difficulty,
            "success_chance": success_chance,
            "stress_penalty": stress_penalty,
            "health_penalty": health_penalty,
            "breakdown_penalty": 30 if npc.is_in_breakdown else 0,
            "quality": NPCSkillsManager._calculate_quality(success, skill_level, difficulty)
        }

    @staticmethod
    def improve_skill(
        npc: NPCState,
        skill_name: str,
        improvement_amount: int = 1
    ) -> Dict[str, Any]:
        """
        Improve an NPC's skill through practice or training.

        Args:
            npc: NPC to improve
            skill_name: Skill to improve
            improvement_amount: Amount to improve (default 1)

        Returns:
            dict: Improvement result
        """
        if skill_name not in npc.skills:
            # Initialize skill at low level
            npc.skills[skill_name] = 20
        
        old_level = npc.skills[skill_name]
        npc.skills[skill_name] = min(100, npc.skills[skill_name] + improvement_amount)
        new_level = npc.skills[skill_name]
        
        logger.info(f"[NPCSkillsManager] {npc.name} improved {skill_name} from {old_level} to {new_level}")
        
        return {
            "skill_name": skill_name,
            "old_level": old_level,
            "new_level": new_level,
            "improvement": improvement_amount
        }

    @staticmethod
    def get_npc_skill_summary(npc: NPCState) -> Dict[str, Any]:
        """
        Get summary of NPC's skills.

        Args:
            npc: NPC to summarize

        Returns:
            dict: Skill summary
        """
        if not npc.skills:
            return {
                "npc_id": npc.id,
                "npc_name": npc.name,
                "skills": {},
                "primary_skills": [],
                "skill_count": 0
            }
        
        # Sort skills by level
        sorted_skills = sorted(npc.skills.items(), key=lambda x: x[1], reverse=True)
        
        # Primary skills (top 3)
        primary_skills = [skill for skill, level in sorted_skills[:3] if level >= 50]
        
        return {
            "npc_id": npc.id,
            "npc_name": npc.name,
            "skills": dict(npc.skills),
            "primary_skills": primary_skills,
            "skill_count": len(npc.skills),
            "average_skill_level": sum(npc.skills.values()) / len(npc.skills) if npc.skills else 0
        }

    @staticmethod
    def _get_related_skills(skill_name: str) -> List[str]:
        """Get list of related skills."""
        related_map = {
            "medical": ["science", "investigation"],
            "engineering": ["repair", "science"],
            "repair": ["engineering", "security"],
            "security": ["investigation", "leadership"],
            "investigation": ["science", "security"],
            "science": ["medical", "engineering"],
        }
        return related_map.get(skill_name, [])

    @staticmethod
    def _calculate_quality(
        success: bool,
        skill_level: int,
        difficulty: int
    ) -> str:
        """Calculate action quality based on success and skill/difficulty ratio."""
        if not success:
            return "failure"
        
        skill_diff = skill_level - difficulty
        if skill_diff >= 30:
            return "excellent"
        elif skill_diff >= 15:
            return "good"
        elif skill_diff >= 0:
            return "adequate"
        else:
            return "poor"
