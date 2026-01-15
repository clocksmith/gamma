"""
Ollama integration for SWE Agent.

Provides async interface to Ollama models for both conductor (large models)
and FunctionGemma ring (small function-calling models).

Requirements:
    pip install httpx

Usage:
    # Start Ollama server with models
    ollama pull llama3.1:70b
    ollama pull functiongemma:latest

    # Create agent
    agent = await create_ollama_agent(
        conductor_model="llama3.1:70b",
        fng_model="functiongemma:latest",
        num_nodes=4,
    )
"""

import asyncio
import json
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, AsyncIterator

try:
    import httpx
except ImportError:
    httpx = None


@dataclass
class OllamaConfig:
    """Configuration for Ollama connection."""
    base_url: str = "http://localhost:11434"
    timeout: float = 120.0
    keep_alive: str = "5m"


class OllamaEngine:
    """
    Async Ollama model engine.

    Implements the interface expected by conductor and ring:
    - generate(prompt, max_tokens) -> str
    - generate_stream(prompt, max_tokens) -> AsyncIterator[str]
    """

    def __init__(
        self,
        model_name: str,
        config: Optional[OllamaConfig] = None,
    ):
        if httpx is None:
            raise ImportError("httpx required: pip install httpx")

        self.model_name = model_name
        self.config = config or OllamaConfig()
        self._client: Optional[httpx.AsyncClient] = None
        self.cost_per_1k_tokens = 0.0

    async def _ensure_client(self) -> httpx.AsyncClient:
        """Ensure HTTP client is initialized."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.config.base_url,
                timeout=httpx.Timeout(self.config.timeout),
            )
        return self._client

    async def close(self) -> None:
        """Close HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None

    async def generate(
        self,
        prompt: str,
        max_tokens: int = 1024,
        temperature: float = 0.7,
        stop: Optional[List[str]] = None,
    ) -> str:
        """
        Generate completion from Ollama.

        Args:
            prompt: Input prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            stop: Stop sequences

        Returns:
            Generated text
        """
        client = await self._ensure_client()

        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False,
            "options": {
                "num_predict": max_tokens,
                "temperature": temperature,
            },
            "keep_alive": self.config.keep_alive,
        }

        if stop:
            payload["options"]["stop"] = stop

        response = await client.post("/api/generate", json=payload)
        response.raise_for_status()

        data = response.json()
        return data.get("response", "")

    async def generate_stream(
        self,
        prompt: str,
        max_tokens: int = 1024,
        temperature: float = 0.7,
    ) -> AsyncIterator[str]:
        """
        Stream completion from Ollama.

        Yields tokens as they're generated.
        """
        client = await self._ensure_client()

        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": True,
            "options": {
                "num_predict": max_tokens,
                "temperature": temperature,
            },
            "keep_alive": self.config.keep_alive,
        }

        async with client.stream("POST", "/api/generate", json=payload) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if line:
                    try:
                        data = json.loads(line)
                        if "response" in data:
                            yield data["response"]
                        if data.get("done", False):
                            break
                    except json.JSONDecodeError:
                        continue

    async def chat(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = 1024,
        temperature: float = 0.7,
    ) -> str:
        """
        Chat completion using Ollama's chat API.

        Args:
            messages: List of {"role": "user"|"assistant"|"system", "content": "..."}
            max_tokens: Maximum tokens
            temperature: Sampling temperature

        Returns:
            Assistant's response
        """
        client = await self._ensure_client()

        payload = {
            "model": self.model_name,
            "messages": messages,
            "stream": False,
            "options": {
                "num_predict": max_tokens,
                "temperature": temperature,
            },
            "keep_alive": self.config.keep_alive,
        }

        response = await client.post("/api/chat", json=payload)
        response.raise_for_status()

        data = response.json()
        return data.get("message", {}).get("content", "")

    async def list_models(self) -> List[str]:
        """List available models in Ollama."""
        client = await self._ensure_client()
        response = await client.get("/api/tags")
        response.raise_for_status()

        data = response.json()
        return [m["name"] for m in data.get("models", [])]

    async def pull_model(self, model_name: Optional[str] = None) -> bool:
        """Pull a model from Ollama registry."""
        client = await self._ensure_client()
        name = model_name or self.model_name

        payload = {"name": name, "stream": False}
        response = await client.post("/api/pull", json=payload)

        return response.status_code == 200


async def create_ollama_agent(
    conductor_model: str = "llama3.1:70b",
    fng_model: str = "functiongemma:latest",
    num_nodes: int = 4,
    ollama_url: str = "http://localhost:11434",
    config: Optional["AgentConfig"] = None,
) -> "SWEAgentV2":
    """
    Create SWE agent with Ollama models.

    Args:
        conductor_model: Large model for conductor (e.g., llama3.1:70b)
        fng_model: Small model for FunctionGemma ring
        num_nodes: Number of FnG ring nodes
        ollama_url: Ollama API URL
        config: Agent configuration

    Returns:
        Configured SWEAgentV2 instance

    Example:
        agent = await create_ollama_agent(
            conductor_model="llama3.1:70b",
            fng_model="gemma2:2b",
            num_nodes=4,
        )
        result = await agent.solve("Fix the auth bug")
    """
    from ..agent import SWEAgentV2, AgentConfig

    ollama_config = OllamaConfig(base_url=ollama_url)

    # Create conductor engine
    conductor = OllamaEngine(conductor_model, ollama_config)

    # Create FnG ring engines (all share same model, different instances)
    fng_models = [
        OllamaEngine(fng_model, ollama_config)
        for _ in range(num_nodes)
    ]

    # Verify models are available
    try:
        available = await conductor.list_models()
        if conductor_model not in available:
            print(f"Warning: {conductor_model} not found. Available: {available}")
            print(f"Run: ollama pull {conductor_model}")
        if fng_model not in available:
            print(f"Warning: {fng_model} not found. Available: {available}")
            print(f"Run: ollama pull {fng_model}")
    except Exception as e:
        print(f"Warning: Could not verify models: {e}")
        print("Is Ollama running? Start with: ollama serve")

    return SWEAgentV2(conductor, fng_models, config or AgentConfig())


async def check_ollama_available(url: str = "http://localhost:11434") -> bool:
    """Check if Ollama server is running."""
    if httpx is None:
        return False

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{url}/api/tags")
            return response.status_code == 200
    except Exception:
        return False
