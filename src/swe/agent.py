"""
SWE Agent v2 - Minimal architecture with FunctionGemma ring.

Architecture:
    CONDUCTOR (Large Model)
        │
        ├── Reasons about task
        ├── Dispatches to FnG ring
        ├── Receives streaming results
        ├── Synthesizes tools on-the-fly
        └── Writes final solution
            │
            ▼
    FUNCTIONGEMMA RING (Parallel)
        │
        ├── N nodes run in parallel
        ├── Results pass around ring
        ├── Scores until threshold met
        └── Streams back to conductor

Features (matching mini-swe-agent):
- Message history tracking
- Cost/step limits
- Jinja2 templates
- Trajectory saving
- Interactive REPL
- Proper exception hierarchy
"""

import asyncio
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from .ring.fng_ring import FunctionGemmaRing, RingConfig
from .conductor.streaming import StreamingConductor
from .tools.scripts import load_tools
from .core.history import History
from .core.trajectory import Trajectory, save_trajectory
from .core.exceptions import (
    CostLimitExceeded,
    StepLimitExceeded,
    Submitted,
    TerminatingException,
)


@dataclass
class AgentConfig:
    """Agent configuration."""
    # Ring settings
    ring_nodes: int = 4
    ring_max_rounds: int = 10
    default_threshold: float = 0.8
    plateau_patience: int = 2
    plateau_epsilon: float = 0.02
    ring_shard_max_items: int = 5
    ring_preview_limit: int = 200
    ring_full_result_top_k: int = 2
    ring_full_result_limit: int = 1000

    # Limits
    step_limit: int = 0  # 0 = unlimited
    cost_limit: float = 10.0  # 0 = unlimited

    # Paths
    tools_dir: Optional[str] = None
    work_dir: str = "/tmp/swe-agent-v2"
    output_dir: Optional[str] = None

    # Behavior
    save_trajectory: bool = True
    interactive: bool = False

    # Memory
    memory_enabled: bool = True
    memory_path: Optional[str] = None
    memory_top_k: int = 3
    memory_min_score: float = 0.25
    memory_max_items: int = 41616
    memory_semantic: bool = True
    memory_embedder_model: str = "all-MiniLM-L6-v2"


class TrackingModel:
    """Proxy model that records history and cost."""

    def __init__(self, model, history_getter, tag: str, check_limits):
        self._model = model
        self._history_getter = history_getter
        self._tag = tag
        self._check_limits = check_limits
        self.model_name = getattr(model, "model_name", "unknown")
        self.cost_per_1k_tokens = getattr(model, "cost_per_1k_tokens", 0.0)

    def _estimate_tokens(self, text: str) -> int:
        if not text:
            return 0
        if hasattr(self._model, "encode"):
            try:
                tokens, _ = self._model.encode(text)
                return len(tokens)
            except Exception:
                pass
        return max(1, len(text) // 4)

    def _record(self, kind: str, text: str) -> None:
        history = self._history_getter()
        if history is None:
            return
        preview = text[:200] if text else ""
        history.add_observation(
            f"{self._tag} {kind}",
            metadata={"preview": preview, "chars": len(text) if text else 0},
        )

    def _record_cost(self, tokens: int) -> None:
        history = self._history_getter()
        if history is None:
            return
        cost = (tokens / 1000.0) * float(self.cost_per_1k_tokens or 0.0)
        history.add_cost(tokens, cost)
        history.increment_step()
        self._check_limits()

    async def generate(self, prompt: str, **kwargs) -> str:
        self._record("prompt", prompt)
        response = await self._model.generate(prompt, **kwargs)
        self._record("response", response)
        tokens = self._estimate_tokens(prompt) + self._estimate_tokens(response)
        self._record_cost(tokens)
        return response

    async def chat(self, messages, **kwargs) -> str:
        self._record("chat_prompt", str(messages)[:500])
        response = await self._model.chat(messages, **kwargs)
        self._record("chat_response", response)
        tokens = self._estimate_tokens(str(messages)) + self._estimate_tokens(response)
        self._record_cost(tokens)
        return response

    def __getattr__(self, name):
        return getattr(self._model, name)


class SWEAgentV2:
    """
    SWE agent with conductor + FnG ring.

    Usage:
        agent = SWEAgentV2(conductor_model, fng_models)
        solution = await agent.solve("Fix the auth bug in login.py")
    """

    def __init__(
        self,
        conductor_model,  # Large model (Claude, Llama 70B)
        fng_models: List[Any],  # List of FunctionGemma instances
        config: Optional[AgentConfig] = None,
    ):
        self.config = config or AgentConfig()
        self.history = History()
        self.conductor_model = TrackingModel(
            conductor_model,
            history_getter=lambda: self.history,
            tag="conductor",
            check_limits=self.check_limits,
        )
        self.fng_models = [
            TrackingModel(
                model,
                history_getter=lambda: self.history,
                tag=f"fng:{i}",
                check_limits=self.check_limits,
            )
            for i, model in enumerate(fng_models)
        ]

        # Create ring
        ring_config = RingConfig(
            num_nodes=len(fng_models),
            max_rounds=self.config.ring_max_rounds,
            default_threshold=self.config.default_threshold,
            plateau_patience=self.config.plateau_patience,
            plateau_epsilon=self.config.plateau_epsilon,
            shard_max_items=self.config.ring_shard_max_items,
            preview_limit=self.config.ring_preview_limit,
            full_result_top_k=self.config.ring_full_result_top_k,
            full_result_limit=self.config.ring_full_result_limit,
        )
        self.ring = FunctionGemmaRing(self.fng_models, ring_config)
        self.ring.set_stream_callback(self._on_ring_output)

        # Load tools
        tools_dir = Path(self.config.tools_dir) if self.config.tools_dir else None
        for name, executor in load_tools(tools_dir).items():
            self.ring.register_tool(name, executor)

        # Create conductor
        self.conductor = StreamingConductor(self.conductor_model, self.ring)

        # Tracking
        self.trajectory: Optional[Trajectory] = None
        self.memory = self._init_memory()

    def check_limits(self) -> None:
        """Check if limits exceeded."""
        if self.config.step_limit > 0 and self.history.n_steps >= self.config.step_limit:
            raise StepLimitExceeded(self.history.n_steps, self.config.step_limit)
        if self.config.cost_limit > 0 and self.history.total_cost >= self.config.cost_limit:
            raise CostLimitExceeded(self.history.total_cost, self.config.cost_limit)

    def _on_ring_output(self, output) -> None:
        """Record tool calls into history."""
        if not self.history:
            return
        self.history.add_tool_call(
            output.tool_call.tool,
            output.tool_call.args,
            output.result,
            score=output.score,
        )
        self.history.increment_step()
        self.check_limits()

    def _init_memory(self):
        """Initialize semantic memory store if enabled."""
        if not self.config.memory_enabled:
            return None

        from .core.memory import MemoryStore, SimpleEmbedder, SentenceTransformerEmbedder

        base_dir = self.config.output_dir or self.config.work_dir
        memory_path = self.config.memory_path or str(Path(base_dir) / "memory.jsonl")
        embedder = None
        if self.config.memory_semantic:
            try:
                embedder = SentenceTransformerEmbedder(self.config.memory_embedder_model)
            except Exception:
                embedder = SimpleEmbedder()
        else:
            embedder = SimpleEmbedder()
        return MemoryStore(
            memory_path,
            embedder=embedder,
            max_items=self.config.memory_max_items,
        )

    async def solve(self, task: str) -> str:
        """Solve a task."""
        # Initialize tracking
        self.history = History()
        self.trajectory = Trajectory(
            task=task,
            model_name=getattr(self.conductor_model, "model_name", "unknown"),
            config=self.config.__dict__,
        )

        exit_status = "Unknown"
        result = ""
        memory_hits = []

        try:
            self.check_limits()
            if self.memory:
                memory_hits = await asyncio.to_thread(
                    self.memory.search,
                    task,
                    self.config.memory_top_k,
                    self.config.memory_min_score,
                )
            result = await self.conductor.solve(
                task,
                memory_hits=memory_hits,
            )
            exit_status = "Submitted"

        except TerminatingException as e:
            exit_status = type(e).__name__
            result = str(e)
            if isinstance(e, Submitted):
                result = e.result

        except Exception as e:
            exit_status = "Error"
            result = str(e)

        finally:
            # Save trajectory
            if self.trajectory:
                self.trajectory.history = self.history
                self.trajectory.finish(exit_status, result)

                if self.config.save_trajectory and self.config.output_dir:
                    import time
                    output_path = Path(self.config.output_dir) / f"traj_{int(time.time())}.json"
                    save_trajectory(self.trajectory, output_path)

            if self.memory and result:
                try:
                    await asyncio.to_thread(
                        self.memory.add,
                        text=task,
                        metadata={
                            "exit_status": exit_status,
                            "result_preview": result[:1000],
                            "memory_hits": [
                                {"score": score, "id": entry.entry_id}
                                for score, entry in memory_hits
                            ],
                        },
                    )
                except Exception:
                    pass

        return result


# --- Factories ---

def create_agent_mock(config: Optional[AgentConfig] = None) -> SWEAgentV2:
    """Create agent with mock models for testing."""
    from .testing import MockEngine

    conductor = MockEngine("conductor:mock")
    fng_models = [MockEngine(f"fng:{i}") for i in range(4)]

    return SWEAgentV2(conductor, fng_models, config)


async def create_agent_ollama(
    conductor_model: str = "llama3.1:70b",
    fng_model: str = "functiongemma:latest",
    num_nodes: int = 4,
    config: Optional[AgentConfig] = None,
) -> SWEAgentV2:
    """Create agent with Ollama models."""
    from .integrations.ollama import create_ollama_agent
    return await create_ollama_agent(
        conductor_model=conductor_model,
        fng_model=fng_model,
        num_nodes=num_nodes,
        config=config,
    )



# --- CLI ---

def main():
    """CLI entry point with interactive support."""
    import argparse

    parser = argparse.ArgumentParser(
        description="SWE Agent v2 - Conductor + FunctionGemma Ring",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python -m gamma.src.swe.agent --mock "Fix the auth bug"
    python -m gamma.src.swe.agent --mock -i  # Interactive mode
        """,
    )
    parser.add_argument("task", nargs="?", help="Task to solve")
    parser.add_argument("--mock", action="store_true", help="Use mock models")
    parser.add_argument("--ollama", action="store_true", help="Use Ollama models")
    parser.add_argument("-i", "--interactive", action="store_true", help="Interactive REPL mode")
    parser.add_argument("-l", "--cost-limit", type=float, default=10.0, help="Cost limit")
    parser.add_argument("-o", "--output", help="Output directory for trajectories")
    parser.add_argument("--conductor-model", default="gptoss-20b", help="Conductor model name")
    parser.add_argument("--fng-model", default="functiongemma:latest", help="FnG model name")

    args = parser.parse_args()

    # Create config
    config = AgentConfig(
        cost_limit=args.cost_limit,
        output_dir=args.output,
        interactive=args.interactive,
    )

    # Create agent
    if args.mock:
        agent = create_agent_mock(config)
    elif args.ollama:
        agent = asyncio.run(create_agent_ollama(
            conductor_model=args.conductor_model,
            fng_model=args.fng_model,
            num_nodes=config.ring_nodes,
            config=config,
        ))
    else:
        print("Choose one: --mock or --ollama")
        return 1

    # Interactive mode
    if args.interactive:
        from .core.repl import run_interactive
        run_interactive(agent)
        return 0

    # Single task mode
    if not args.task:
        parser.print_help()
        return 1

    print(f"Task: {args.task}")
    print("Running...")

    solution = asyncio.run(agent.solve(args.task))

    print("\n--- Solution ---")
    print(solution)
    return 0


if __name__ == "__main__":
    exit(main())
