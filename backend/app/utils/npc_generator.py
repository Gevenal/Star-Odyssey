"""NPC generation with random personalities."""
import random
from typing import List, Dict, Optional
from app.models.npc import NPCState, PersonalityTraits, NPCRelationship
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

    def generate_npc(self, role: str, npc_id: Optional[str] = None) -> NPCState:
        """Generate single NPC from template."""
        if role not in self.templates:
            raise ValueError(f"Unknown NPC role: {role}")

        template = self.templates[role]
        personality = self._generate_personality(template)

        if not self._check_trait_compatibility(personality):
            logger.warning(f"Generated incompatible traits for {role}, regenerating...")
            personality = self._generate_personality(template)

        npc_id = npc_id or f"{role.lower().replace(' ', '_')}_{random.randint(1000, 9999)}"

        npc = NPCState(
            id=npc_id,
            name=template.name,
            role=role,
            location=template.starting_location,
            alive=True,
            health=100,
            stress_level=template.initial_stress or random.randint(10, 30),
            personality=personality,
            relationships={},
            goals=template.initial_goals.copy(),
            current_activity=None,
        )

        logger.info(f"Generated NPC: {npc.name} ({role})")
        return npc

    def generate_full_crew(self, roles: List[str]) -> Dict[str, NPCState]:
        """Generate complete crew."""
        npcs = {}

        for role in roles:
            npc = self.generate_npc(role)
            npcs[npc.id] = npc

        npcs = self.generate_relationships(npcs)

        logger.info(f"Generated crew of {len(npcs)} NPCs")
        return npcs

    def generate_relationships(self, npcs: Dict[str, NPCState]) -> Dict[str, NPCState]:
        """Generate inter-NPC relationships with history anchors."""
        npc_list = list(npcs.values())

        for i, npc1 in enumerate(npc_list):
            for npc2 in npc_list[i + 1:]:
                trust_level = self._calculate_initial_trust(npc1, npc2)
                anchor = self._generate_relationship_anchor(npc1, npc2, trust_level)

                npc1.relationships[npc2.id] = NPCRelationship(
                    target_npc_id=npc2.id,
                    trust_level=trust_level,
                    relationship_history=[anchor]
                )

                npc2.relationships[npc1.id] = NPCRelationship(
                    target_npc_id=npc1.id,
                    trust_level=trust_level,
                    relationship_history=[anchor]
                )

        return npcs

    def _generate_personality(self, template: NPCTemplateConfig) -> PersonalityTraits:
        """Generate personality from template."""
        role_weights = template.personality_weights or {}

        return PersonalityTraits(
            core_value=self._select_weighted_trait("core_value", role_weights),
            social_style=self._select_weighted_trait("social_style", role_weights),
            stress_response=self._select_weighted_trait("stress_response", role_weights),
            decision_making=self._select_weighted_trait("decision_making", role_weights),
            morality=self._select_weighted_trait("morality", role_weights),
            quirks=self._select_random_quirks(),
        )

    def _select_weighted_trait(self, dimension: str, role_weights: Dict[str, float]) -> str:
        """Select trait with role-based weighting."""
        if dimension not in self.trait_pool:
            raise ValueError(f"Unknown trait dimension: {dimension}")

        traits = self.trait_pool[dimension]
        weights = [role_weights.get(f"{dimension}.{t.trait_id}", 1.0) for t in traits]
        total = sum(weights)
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
        return True  # Simplified for now

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
        """Generate backstory for relationship."""
        if trust_level >= 70:
            templates = [
                f"{npc1.name} and {npc2.name} served together successfully.",
                f"{npc1.name} helped {npc2.name} through a crisis.",
            ]
        elif trust_level >= 40:
            templates = [
                f"{npc1.name} and {npc2.name} are cautiously friendly.",
                f"Both have mutual professional respect.",
            ]
        else:
            templates = [
                f"{npc1.name} and {npc2.name} had a disagreement.",
                f"They have conflicting work philosophies.",
            ]

        return random.choice(templates)
