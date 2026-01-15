"""
Trajectory saving and loading.

Saves full execution trace for debugging and analysis.
"""

import json
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional

from .history import History


@dataclass
class RingRound:
    """Single round of ring execution."""
    round_num: int
    node_outputs: List[Dict[str, Any]]
    best_score: float
    threshold: float
    threshold_met: bool
    duration_ms: float


@dataclass
class Step:
    """Single step in conductor's plan."""
    step_num: int
    query: str
    threshold: float
    ring_rounds: List[RingRound]
    final_score: float
    result: Any
    duration_ms: float


@dataclass
class Trajectory:
    """
    Full execution trajectory.

    Captures everything for debugging and replay.
    """
    # Task info
    task: str
    task_id: Optional[str] = None

    # Execution trace
    steps: List[Step] = field(default_factory=list)
    history: Optional[History] = None

    # Results
    exit_status: Optional[str] = None
    result: Optional[str] = None
    patch: Optional[str] = None

    # Metrics
    total_cost: float = 0.0
    total_tokens: int = 0
    total_rounds: int = 0
    total_tool_calls: int = 0
    duration_seconds: float = 0.0

    # Metadata
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    model_name: Optional[str] = None
    config: Dict[str, Any] = field(default_factory=dict)
    extra_info: Dict[str, Any] = field(default_factory=dict)

    # Tools used
    tools_used: Dict[str, int] = field(default_factory=dict)
    tools_synthesized: List[str] = field(default_factory=list)

    def add_step(self, step: Step) -> None:
        """Add a step to trajectory."""
        self.steps.append(step)
        self.total_rounds += len(step.ring_rounds)
        for rr in step.ring_rounds:
            self.total_tool_calls += len(rr.node_outputs)

    def finish(
        self,
        exit_status: str,
        result: Optional[str] = None,
        patch: Optional[str] = None,
    ) -> None:
        """Mark trajectory as complete."""
        self.exit_status = exit_status
        self.result = result
        self.patch = patch
        self.end_time = time.time()
        self.duration_seconds = self.end_time - self.start_time

        if self.history:
            self.total_cost = self.history.total_cost
            self.total_tokens = self.history.total_tokens

    def to_dict(self) -> Dict[str, Any]:
        """Serialize trajectory."""
        d = {
            "task": self.task,
            "task_id": self.task_id,
            "steps": [asdict(s) for s in self.steps],
            "exit_status": self.exit_status,
            "result": self.result,
            "patch": self.patch,
            "metrics": {
                "total_cost": self.total_cost,
                "total_tokens": self.total_tokens,
                "total_rounds": self.total_rounds,
                "total_tool_calls": self.total_tool_calls,
                "duration_seconds": self.duration_seconds,
            },
            "timing": {
                "start_time": self.start_time,
                "end_time": self.end_time,
            },
            "model_name": self.model_name,
            "config": self.config,
            "tools_used": self.tools_used,
            "tools_synthesized": self.tools_synthesized,
            "extra_info": self.extra_info,
        }
        if self.history:
            d["history"] = self.history.to_dict()
        return d

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Trajectory":
        """Deserialize trajectory."""
        traj = cls(
            task=d["task"],
            task_id=d.get("task_id"),
            exit_status=d.get("exit_status"),
            result=d.get("result"),
            patch=d.get("patch"),
            model_name=d.get("model_name"),
            config=d.get("config", {}),
            extra_info=d.get("extra_info", {}),
            tools_used=d.get("tools_used", {}),
            tools_synthesized=d.get("tools_synthesized", []),
        )

        metrics = d.get("metrics", {})
        traj.total_cost = metrics.get("total_cost", 0.0)
        traj.total_tokens = metrics.get("total_tokens", 0)
        traj.total_rounds = metrics.get("total_rounds", 0)
        traj.total_tool_calls = metrics.get("total_tool_calls", 0)
        traj.duration_seconds = metrics.get("duration_seconds", 0.0)

        timing = d.get("timing", {})
        traj.start_time = timing.get("start_time", time.time())
        traj.end_time = timing.get("end_time")

        if "history" in d:
            traj.history = History.from_dict(d["history"])

        # Reconstruct steps (simplified - loses dataclass structure)
        # Full reconstruction would need Step.from_dict
        traj.steps = []

        return traj


def save_trajectory(
    trajectory: Trajectory,
    path: Path,
    pretty: bool = True,
) -> None:
    """Save trajectory to JSON file."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w") as f:
        if pretty:
            json.dump(trajectory.to_dict(), f, indent=2, default=str)
        else:
            json.dump(trajectory.to_dict(), f, default=str)


def load_trajectory(path: Path) -> Trajectory:
    """Load trajectory from JSON file."""
    with open(path) as f:
        return Trajectory.from_dict(json.load(f))
