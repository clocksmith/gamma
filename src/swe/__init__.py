"""
SWE Agent v2 - Minimal architecture with FunctionGemma ring.

Architecture:
    CONDUCTOR (Large Model) - reasons, reads/writes code, synthesizes tools
        │
        ▼
    FUNCTIONGEMMA RING (Parallel) - fast tool search with streaming

Usage:
    from gamma.src.swe import SWEAgentV2, create_agent_mock

    agent = create_agent_mock()
    solution = await agent.solve("Fix the auth bug")
"""

from .agent import SWEAgentV2, AgentConfig, create_agent_mock
from .ring import FunctionGemmaRing, RingConfig, RingResult
from .conductor.streaming import StreamingConductor

__all__ = [
    # v2 API
    "SWEAgentV2",
    "AgentConfig",
    "create_agent_mock",
    "FunctionGemmaRing",
    "RingConfig",
    "RingResult",
    "StreamingConductor",
]

__version__ = "2.0.0"
