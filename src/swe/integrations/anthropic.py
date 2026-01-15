"""
Anthropic integration for SWE Agent.

Provides async interface to Claude models for the conductor.
Uses Claude for high-quality reasoning and code generation.

Requirements:
    pip install anthropic

Usage:
    export ANTHROPIC_API_KEY="sk-..."

    agent = await create_anthropic_agent(
        conductor_model="claude-sonnet-4-20250514",
    )
"""

import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

try:
    import anthropic
except ImportError:
    anthropic = None


@dataclass
class AnthropicConfig:
    """Configuration for Anthropic API."""
    api_key: Optional[str] = None
    max_retries: int = 2
    timeout: float = 120.0


class AnthropicEngine:
    """
    Async Anthropic Claude engine.

    Implements the interface expected by conductor:
    - generate(prompt, max_tokens) -> str
    """

    # Model mapping for convenience names
    MODEL_ALIASES = {
        "claude-3-opus": "claude-3-opus-20240229",
        "claude-3-sonnet": "claude-sonnet-4-20250514",
        "claude-3-haiku": "claude-3-haiku-20240307",
        "claude-3.5-sonnet": "claude-sonnet-4-20250514",
        "sonnet": "claude-sonnet-4-20250514",
        "opus": "claude-3-opus-20240229",
        "haiku": "claude-3-haiku-20240307",
    }

    def __init__(
        self,
        model_name: str = "claude-sonnet-4-20250514",
        config: Optional[AnthropicConfig] = None,
    ):
        if anthropic is None:
            raise ImportError("anthropic required: pip install anthropic")

        self.config = config or AnthropicConfig()

        # Resolve model alias
        self.model_name = self.MODEL_ALIASES.get(model_name, model_name)

        # Get API key
        api_key = self.config.api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY required. Set via env or config.api_key"
            )

        self._client = anthropic.AsyncAnthropic(
            api_key=api_key,
            max_retries=self.config.max_retries,
            timeout=self.config.timeout,
        )

    async def generate(
        self,
        prompt: str,
        max_tokens: int = 4096,
        temperature: float = 0.7,
        system: Optional[str] = None,
        stop: Optional[List[str]] = None,
    ) -> str:
        """
        Generate completion from Claude.

        Args:
            prompt: Input prompt (becomes user message)
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            system: System prompt
            stop: Stop sequences

        Returns:
            Generated text
        """
        messages = [{"role": "user", "content": prompt}]

        kwargs = {
            "model": self.model_name,
            "max_tokens": max_tokens,
            "messages": messages,
            "temperature": temperature,
        }

        if system:
            kwargs["system"] = system

        if stop:
            kwargs["stop_sequences"] = stop

        response = await self._client.messages.create(**kwargs)

        # Extract text from response
        if response.content and len(response.content) > 0:
            return response.content[0].text

        return ""

    async def chat(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = 4096,
        temperature: float = 0.7,
        system: Optional[str] = None,
    ) -> str:
        """
        Chat completion with Claude.

        Args:
            messages: List of {"role": "user"|"assistant", "content": "..."}
            max_tokens: Maximum tokens
            temperature: Sampling temperature
            system: System prompt

        Returns:
            Assistant's response
        """
        kwargs = {
            "model": self.model_name,
            "max_tokens": max_tokens,
            "messages": messages,
            "temperature": temperature,
        }

        if system:
            kwargs["system"] = system

        response = await self._client.messages.create(**kwargs)

        if response.content and len(response.content) > 0:
            return response.content[0].text

        return ""

    @property
    def input_cost_per_1k(self) -> float:
        """Approximate input cost per 1K tokens."""
        costs = {
            "claude-3-opus-20240229": 0.015,
            "claude-sonnet-4-20250514": 0.003,
            "claude-3-haiku-20240307": 0.00025,
        }
        return costs.get(self.model_name, 0.003)

    @property
    def output_cost_per_1k(self) -> float:
        """Approximate output cost per 1K tokens."""
        costs = {
            "claude-3-opus-20240229": 0.075,
            "claude-sonnet-4-20250514": 0.015,
            "claude-3-haiku-20240307": 0.00125,
        }
        return costs.get(self.model_name, 0.015)


async def create_anthropic_agent(
    conductor_model: str = "claude-sonnet-4-20250514",
    fng_model: str = "ollama:gemma2:2b",
    num_nodes: int = 4,
    config: Optional["AgentConfig"] = None,
) -> "SWEAgentV2":
    """
    Create SWE agent with Claude conductor and Ollama FnG ring.

    This is a hybrid setup:
    - Conductor: Claude (high-quality reasoning)
    - Ring: Ollama FunctionGemma (fast, local, cheap)

    Args:
        conductor_model: Claude model for conductor
        fng_model: Model for FnG ring (format: "ollama:model" or just "model")
        num_nodes: Number of FnG ring nodes
        config: Agent configuration

    Returns:
        Configured SWEAgentV2 instance

    Example:
        agent = await create_anthropic_agent(
            conductor_model="sonnet",
            fng_model="ollama:gemma2:2b",
        )
        result = await agent.solve("Fix the auth bug")
    """
    from ..agent import SWEAgentV2, AgentConfig
    from .ollama import OllamaEngine, OllamaConfig

    # Create Claude conductor
    conductor = AnthropicEngine(conductor_model)

    # Parse FnG model (strip "ollama:" prefix if present)
    if fng_model.startswith("ollama:"):
        fng_model = fng_model[7:]

    # Create Ollama FnG ring
    ollama_config = OllamaConfig()
    fng_models = [
        OllamaEngine(fng_model, ollama_config)
        for _ in range(num_nodes)
    ]

    return SWEAgentV2(conductor, fng_models, config or AgentConfig())


async def create_claude_only_agent(
    model: str = "claude-sonnet-4-20250514",
    config: Optional["AgentConfig"] = None,
) -> "SWEAgentV2":
    """
    Create agent using Claude for both conductor and ring.

    More expensive but doesn't require local Ollama.
    Uses Haiku for the ring nodes (cheaper, faster).

    Args:
        model: Claude model for conductor
        config: Agent configuration

    Returns:
        Configured SWEAgentV2 instance
    """
    from ..agent import SWEAgentV2, AgentConfig

    # Conductor uses the specified model
    conductor = AnthropicEngine(model)

    # Ring uses Haiku (fastest, cheapest Claude)
    fng_models = [
        AnthropicEngine("claude-3-haiku-20240307")
        for _ in range(4)
    ]

    return SWEAgentV2(conductor, fng_models, config or AgentConfig())
