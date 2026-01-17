"""Google Gemini API client."""
from typing import AsyncGenerator, Optional


class GeminiClient:
    """Client for Google Gemini API (Pro and Flash models)."""

    def __init__(self, api_key: str):
        """
        Initialize Gemini client.

        Args:
            api_key: Google Gemini API key
        """
        self.api_key = api_key
        self.pro_model = None  # TODO: Initialize pro model
        self.flash_model = None  # TODO: Initialize flash model

    async def generate_narration(
        self,
        prompt: str,
        stream: bool = False,
        temperature: float = 0.8
    ) -> str | AsyncGenerator[str, None]:
        """
        Generate narration using Gemini Pro.

        Args:
            prompt: Full prompt with context
            stream: Whether to stream response
            temperature: Generation temperature

        Returns:
            str or AsyncGenerator: Generated text or stream
        """
        raise NotImplementedError

    async def generate_npc_response(
        self,
        prompt: str,
        temperature: float = 0.7
    ) -> str:
        """
        Generate NPC dialogue/action using Gemini Flash.

        Args:
            prompt: NPC behavior prompt
            temperature: Generation temperature

        Returns:
            str: NPC response
        """
        raise NotImplementedError

    async def generate_world_event(
        self,
        prompt: str,
        temperature: float = 0.7
    ) -> str:
        """
        Generate world event using Gemini Flash.

        Args:
            prompt: World state prompt
            temperature: Generation temperature

        Returns:
            str: World event description
        """
        raise NotImplementedError

    async def close(self):
        """Close client connections."""
        pass
