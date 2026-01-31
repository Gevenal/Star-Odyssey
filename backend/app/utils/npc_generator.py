"""NPC generation with random personalities."""
import random
from typing import List, Dict, Optional, Any
from app.models.npc import NPCState, PersonalityTraits, NPCRelationship, NPCSecret
from app.game_data.schemas import NPCTemplateConfig, PersonalityTraitDefinition
from app.utils.logger import get_logger

logger = get_logger(__name__)


class NPCGenerator:
    """Generates NPCs with randomized personalities."""

    def __init__(
        self,
        trait_pool: Dict[str, List[PersonalityTraitDefinition]],
        npc_templates: Dict[str, NPCTemplateConfig]
    ):
        self.trait_pool = trait_pool
        self.templates = npc_templates
        # Build trait lookup by ID for quick access
        self._trait_lookup: Dict[str, PersonalityTraitDefinition] = {}
        for category, traits in trait_pool.items():
            for trait in traits:
                self._trait_lookup[trait.trait_id] = trait

    def generate_npc(self, role: str, npc_id: Optional[str] = None) -> NPCState:
        """Generate single NPC from template."""
        if role not in self.templates:
            raise ValueError(f"Unknown NPC role: {role}")

        template = self.templates[role]
        personality = self._generate_personality(template)

        if not self._check_trait_compatibility(personality):
            logger.warning(f"Generated incompatible traits for {role}, regenerating...")
            personality = self._generate_personality(template)

        npc_id = npc_id or f"{template.template_id}_{random.randint(1000, 9999)}"

        # Convert secrets from template
        secrets = []
        for secret_data in template.secrets:
            secrets.append(NPCSecret(**secret_data))
        
        # Extract breaking point configuration
        breaking_point_threshold = None
        breakdown_trait = None
        breakdown_behavior = None
        if hasattr(template, 'breaking_point') and template.breaking_point:
            breaking_point_threshold = template.breaking_point.get('stress_threshold')
            breakdown_trait = template.breaking_point.get('breakdown_trait')
            breakdown_behavior = template.breaking_point.get('breakdown_behavior')

        # Get starting inventory from template
        starting_inventory = getattr(template, 'starting_inventory', []) or []
        
        # Initialize skills
        from app.utils.npc_skills_manager import NPCSkillsManager
        # Create temporary NPC-like object for skill initialization
        class TempNPC:
            def __init__(self, role, personality):
                self.role = role
                self.personality = personality
        temp_npc = TempNPC(template.role, personality)
        skills = NPCSkillsManager.initialize_npc_skills(temp_npc)
        
        npc = NPCState(
            id=npc_id,
            name=template.name,
            role=template.role,
            location=template.starting_location,
            alive=True,
            health=template.starting_health,
            stress_level=template.starting_stress,
            personality=personality,
            relationships={},
            goals=template.initial_goals.copy(),
            secrets=secrets,
            hidden_agenda=template.hidden_agenda,
            hidden_agenda_type=getattr(template, 'hidden_agenda_type', None),
            hidden_agenda_conflicts_with_player=getattr(template, 'hidden_agenda_conflicts_with_player', False),
            current_activity=None,
            inventory=starting_inventory.copy(),
            breaking_point_threshold=breaking_point_threshold,
            breakdown_trait=breakdown_trait,
            breakdown_behavior=breakdown_behavior,
            is_in_breakdown=False,
            skills=skills
        )
        
        # Initialize breakdown state
        npc.update_breakdown_state()

        logger.info(f"Generated NPC: {npc.name} ({role})")
        return npc

    def generate_full_crew(
        self, 
        roles: List[str],
        initial_relationships: Optional[Dict[str, Dict[str, Any]]] = None
    ) -> Dict[str, NPCState]:
        """Generate complete crew.
        
        Args:
            roles: List of NPC role IDs to generate
            initial_relationships: Optional initial relationship seeds from state_variables.json
                Format: {"NPC Name": {"Other NPC Name": trust_level, "secret_knowledge": [...], ...}}
        """
        npcs = {}

        for role in roles:
            npc = self.generate_npc(role)
            npcs[npc.id] = npc

        npcs = self.generate_relationships(npcs, initial_relationships=initial_relationships)

        logger.info(f"Generated crew of {len(npcs)} NPCs")
        return npcs

    def generate_relationships(
        self, 
        npcs: Dict[str, NPCState],
        initial_relationships: Optional[Dict[str, Dict[str, Any]]] = None
    ) -> Dict[str, NPCState]:
        """Generate inter-NPC relationships with history anchors.
        
        Args:
            npcs: Dictionary of NPCs to generate relationships for
            initial_relationships: Optional initial relationship seeds from state_variables.json
                Format: {"NPC Name": {"Other NPC Name": trust_level, "secret_knowledge": [...], ...}}
        """
        npc_list = list(npcs.values())
        # Build name to ID lookup
        name_to_id = {npc.name: npc.id for npc in npc_list}
        name_to_npc = {npc.name: npc for npc in npc_list}

        for i, npc1 in enumerate(npc_list):
            for npc2 in npc_list[i + 1:]:
                # Check if there's a preset relationship in initial_relationships
                trust_level = None
                secret_knowledge = []
                voice_style = None
                
                if initial_relationships:
                    # Check npc1 -> npc2
                    if npc1.name in initial_relationships:
                        rel_data = initial_relationships[npc1.name]
                        if npc2.name in rel_data:
                            trust_val = rel_data[npc2.name]
                            if isinstance(trust_val, (int, float)):
                                trust_level = int(trust_val)
                            secret_knowledge = rel_data.get("secret_knowledge", [])
                            voice_style = rel_data.get("voice_style")
                    
                    # Check npc2 -> npc1 (reverse direction)
                    if trust_level is None and npc2.name in initial_relationships:
                        rel_data = initial_relationships[npc2.name]
                        if npc1.name in rel_data:
                            trust_val = rel_data[npc1.name]
                            if isinstance(trust_val, (int, float)):
                                trust_level = int(trust_val)
                            if not secret_knowledge:
                                secret_knowledge = rel_data.get("secret_knowledge", [])
                            if not voice_style:
                                voice_style = rel_data.get("voice_style")
                
                # If no preset, calculate randomly
                if trust_level is None:
                    trust_level = self._calculate_initial_trust(npc1, npc2)
                
                # Generate relationship anchor
                anchor = self._generate_relationship_anchor(npc1, npc2, trust_level)

                # Create relationship for npc1 -> npc2
                npc1.relationships[npc2.id] = NPCRelationship(
                    target_npc_id=npc2.id,
                    trust_level=trust_level,
                    relationship_history=[anchor],
                    secret_knowledge=secret_knowledge.copy() if secret_knowledge else [],
                    voice_style=voice_style
                )

                # Create relationship for npc2 -> npc1 (reverse, but trust level may differ)
                # For reverse, check if there's a different preset
                reverse_trust = trust_level
                reverse_secrets = []
                reverse_voice = None
                
                if initial_relationships:
                    if npc2.name in initial_relationships:
                        rel_data = initial_relationships[npc2.name]
                        if npc1.name in rel_data:
                            trust_val = rel_data[npc1.name]
                            if isinstance(trust_val, (int, float)):
                                reverse_trust = int(trust_val)
                            reverse_secrets = rel_data.get("secret_knowledge", [])
                            reverse_voice = rel_data.get("voice_style")
                
                npc2.relationships[npc1.id] = NPCRelationship(
                    target_npc_id=npc1.id,
                    trust_level=reverse_trust,
                    relationship_history=[anchor],
                    secret_knowledge=reverse_secrets.copy() if reverse_secrets else [],
                    voice_style=reverse_voice
                )

        return npcs

    def _generate_personality(self, template: NPCTemplateConfig) -> PersonalityTraits:
        """Generate personality from template."""
        role_weights = getattr(template, 'personality_weights', None) or {}

        # Get speech_pattern from template if specified, otherwise random
        speech_pattern = template.personality_traits.get("speech_pattern")
        if not speech_pattern and "speech_pattern" in self.trait_pool:
            speech_pattern = self._select_random_trait("speech_pattern")
        
        return PersonalityTraits(
            core_value=self._select_weighted_trait("core_value", role_weights),
            social_style=self._select_weighted_trait("social_style", role_weights),
            stress_response=self._select_weighted_trait("stress_response", role_weights),
            decision_making=self._select_weighted_trait("decision_making", role_weights),
            morality=self._select_weighted_trait("morality", role_weights),
            quirks=self._select_random_quirks(),
            speech_pattern=speech_pattern,
        )

    def _select_random_trait(self, dimension: str) -> str:
        """Select random trait from dimension."""
        if dimension not in self.trait_pool:
            raise ValueError(f"Unknown trait dimension: {dimension}")
        
        traits = self.trait_pool[dimension]
        if not traits:
            raise ValueError(f"No traits available for dimension: {dimension}")
        
        selected = random.choice(traits)
        return selected.trait_id

    def _select_weighted_trait(self, dimension: str, role_weights: Dict[str, float]) -> str:
        """Select trait with role-based weighting."""
        if dimension not in self.trait_pool:
            raise ValueError(f"Unknown trait dimension: {dimension}")

        traits = self.trait_pool[dimension]
        weights = [role_weights.get(f"{dimension}.{t.trait_id}", 1.0) for t in traits]
        total = sum(weights)
        if total == 0:
            return self._select_random_trait(dimension)
        
        weights = [w / total for w in weights]
        selected = random.choices(traits, weights=weights, k=1)[0]
        return selected.trait_id

    def _select_random_quirks(self, count: int = 2) -> List[str]:
        """Select random quirks."""
        if "quirks" not in self.trait_pool:
            return []

        quirks = self.trait_pool["quirks"]
        count = min(count, len(quirks))
        selected = random.sample(quirks, count)
        return [q.trait_id for q in selected]

    def _check_trait_compatibility(self, traits: PersonalityTraits) -> bool:
        """Check for incompatible trait combinations."""
        # Get all trait definitions
        trait_defs = {}
        for attr_name in ["core_value", "social_style", "stress_response", "decision_making", "morality"]:
            trait_id = getattr(traits, attr_name)
            if trait_id in self._trait_lookup:
                trait_defs[attr_name] = self._trait_lookup[trait_id]
        
        # Check for incompatible pairs
        for attr1, def1 in trait_defs.items():
            for attr2, def2 in trait_defs.items():
                if attr1 == attr2:
                    continue
                
                # Check if def1's incompatible list contains def2's trait_id
                if def2.trait_id in def1.incompatible_with:
                    logger.debug(f"Incompatible traits: {def1.trait_id} incompatible with {def2.trait_id}")
                    return False
        
        return True

    def _calculate_initial_trust(self, npc1: NPCState, npc2: NPCState) -> int:
        """Calculate initial trust level between NPCs."""
        base_trust = 50

        if npc1.personality.social_style == npc2.personality.social_style:
            base_trust += 10

        if npc1.personality.core_value == npc2.personality.core_value:
            base_trust += 15

        base_trust += random.randint(-15, 15)

        return max(0, min(100, base_trust))

    def _generate_relationship_anchor(
        self,
        npc1: NPCState,
        npc2: NPCState,
        trust_level: int
    ) -> str:
        """Generate rich backstory anchor for relationship."""
        # High trust relationships
        if trust_level >= 70:
            templates = [
                f"{npc1.name} and {npc2.name} served together on a previous mission where they saved each other's lives.",
                f"{npc1.name} helped {npc2.name} through a personal crisis during the voyage, creating a strong bond.",
                f"{npc1.name} and {npc2.name} have been close friends since training academy, trusting each other implicitly.",
                f"During a critical system failure, {npc1.name} and {npc2.name} worked together flawlessly, earning mutual respect.",
            ]
        # Medium trust relationships
        elif trust_level >= 40:
            templates = [
                f"{npc1.name} and {npc2.name} are cautiously friendly, having worked together on routine tasks.",
                f"Both {npc1.name} and {npc2.name} have mutual professional respect, though they keep some distance.",
                f"{npc1.name} and {npc2.name} had a minor disagreement early in the mission but resolved it professionally.",
                f"While {npc1.name} and {npc2.name} don't socialize much, they recognize each other's competence.",
            ]
        # Low trust relationships
        else:
            templates = [
                f"{npc1.name} and {npc2.name} had a significant disagreement about mission priorities early on.",
                f"They have conflicting work philosophies - {npc1.name} prefers {self._get_trait_description(npc1.personality.core_value)} while {npc2.name} values {self._get_trait_description(npc2.personality.core_value)}.",
                f"{npc1.name} suspects {npc2.name} of being unreliable, based on past observations.",
                f"There's tension between {npc1.name} and {npc2.name} due to a misunderstanding that was never fully resolved.",
            ]
        
        return random.choice(templates)
    
    def _get_trait_description(self, trait_id: str) -> str:
        """Get human-readable description of a trait."""
        if trait_id in self._trait_lookup:
            return self._trait_lookup[trait_id].trait_name.lower()
        return trait_id.replace("_", " ").lower()
    
    def get_personality_prompt_instructions(self, npc: NPCState) -> str:
        """Get formatted prompt instructions for NPC's personality.
        
        This is the key method that ensures AI can correctly use personality traits.
        """
        instructions = []
        
        # Get prompt instructions for each trait dimension
        for attr_name in ["core_value", "social_style", "stress_response", "decision_making", "morality"]:
            trait_id = getattr(npc.personality, attr_name)
            if trait_id in self._trait_lookup:
                trait_def = self._trait_lookup[trait_id]
                instructions.append(f"- {trait_def.prompt_instruction}")
        
        # Add speech pattern if present
        if npc.personality.speech_pattern and npc.personality.speech_pattern in self._trait_lookup:
            speech_def = self._trait_lookup[npc.personality.speech_pattern]
            instructions.append(f"- SPEECH STYLE: {speech_def.prompt_instruction}")
        
        # Add quirks if any
        if npc.personality.quirks:
            quirks_text = ", ".join(npc.personality.quirks)
            instructions.append(f"- Notable quirks: {quirks_text}")
        
        return "\n".join(instructions)