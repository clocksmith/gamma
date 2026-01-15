"""Model integrations for SWE Agent."""

from .ollama import OllamaEngine, create_ollama_agent
from .anthropic import AnthropicEngine, create_anthropic_agent

__all__ = [
    "OllamaEngine",
    "create_ollama_agent",
    "AnthropicEngine",
    "create_anthropic_agent",
]
