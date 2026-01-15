"""
Testing utilities for the SWE agent.

Contains mock engines and factories for testing without actual models.
"""

from typing import Any, Callable


class MockEngine:
    """
    Mock LLM engine for testing without actual models.

    Implements the minimal interface expected by experts and conductors:
    - generate(prompt, **kwargs) -> str
    - chat(prompt, **kwargs) -> str
    - encode(text, **kwargs) -> (tokens, attention_mask)
    - decode(tokens, **kwargs) -> str
    - get_special_tokens() -> dict
    """

    def __init__(self, name: str):
        """
        Initialize mock engine.

        Args:
            name: Model identifier (for logging/debugging)
        """
        self.model_name = name
        self._loaded = False
        self.cost_per_1k_tokens = 0.0

    def load(self) -> None:
        """Simulate model loading."""
        self._loaded = True

    async def generate(self, prompt: str, **kwargs) -> str:
        """Generate a mock response."""
        max_tokens = kwargs.get("max_tokens", 100)
        return f"Mock response for: {prompt[:50]}... [max_tokens={max_tokens}]"

    async def chat(self, prompt: str, **kwargs) -> str:
        """Generate a mock chat response."""
        return await self.generate(prompt, **kwargs)

    def encode(self, text: str, **kwargs) -> tuple:
        """Mock tokenization."""
        # Return fake token IDs proportional to text length
        fake_tokens = list(range(1, min(len(text) // 4 + 1, 100)))
        return fake_tokens, None

    def decode(self, tokens: list, **kwargs) -> str:
        """Mock detokenization."""
        return f"mock decoded text ({len(tokens)} tokens)"

    def get_special_tokens(self) -> dict:
        """Return mock special tokens."""
        return {
            "eos_token_id": 0,
            "bos_token_id": 1,
            "pad_token_id": 2,
        }


def create_mock_engine_factory() -> Callable[[str, str], MockEngine]:
    """
    Create a mock engine factory for testing.

    Returns:
        Factory function (engine_name, model_name) -> MockEngine
    """
    def factory(engine_name: str, model_name: str) -> MockEngine:
        engine = MockEngine(f"{engine_name}:{model_name}")
        return engine

    return factory
