"""Tests for NPC generator."""
import pytest
from app.utils.npc_generator import NPCGenerator
from app.models.npc import NPCState


class TestNPCGenerator:
    """Test suite for NPC generation."""

    def test_generate_single_npc(self, mock_game_data_loader):
        """Test generating a single NPC."""
        # TODO: Implement
        # generator = NPCGenerator(trait_pool={}, npc_templates={})
        # npc = generator.generate_npc("Medical Officer")
        # assert isinstance(npc, NPCState)
        # assert npc.role == "Medical Officer"
        pass

    def test_generate_full_crew(self):
        """Test generating complete crew."""
        # TODO: Implement
        # roles = ["Captain", "Medical Officer", "Engineer"]
        # npcs = generator.generate_full_crew(roles)
        # assert len(npcs) == 3
        pass

    def test_personality_trait_selection(self):
        """Test weighted personality trait selection."""
        # TODO: Verify trait selection respects weights
        pass

    def test_trait_compatibility_check(self):
        """Test incompatible trait combinations are detected."""
        # TODO: Create incompatible traits
        # Verify they're rejected
        pass

    def test_relationship_generation(self):
        """Test NPC relationship generation."""
        # TODO: Generate NPCs with relationships
        # Verify bidirectional relationships
        # Verify trust levels are reasonable
        pass

    def test_relationship_anchor_generation(self):
        """Test relationship backstory generation."""
        # TODO: Generate relationships
        # Verify anchors exist and make sense
        pass
