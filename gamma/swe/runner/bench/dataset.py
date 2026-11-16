"""
SWE-bench dataset loader.

Loads tasks from HuggingFace datasets:
- princeton-nlp/SWE-bench_Lite (300 tasks)
- princeton-nlp/SWE-bench_Verified (500 tasks)
- princeton-nlp/SWE-bench (2294 tasks)
"""

from dataclasses import dataclass, field
from typing import Any, Dict, Iterator, List, Optional


@dataclass
class SWEBenchTask:
    """Single SWE-bench task."""
    instance_id: str
    repo: str  # e.g., "django/django"
    base_commit: str
    problem_statement: str
    hints_text: str = ""
    test_patch: str = ""  # Gold test patch
    patch: str = ""  # Gold solution patch
    version: str = ""
    environment_setup_commit: str = ""

    # Populated during run
    repo_path: Optional[str] = None

    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def repo_url(self) -> str:
        """Get full GitHub URL."""
        return f"https://github.com/{self.repo}.git"

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "SWEBenchTask":
        """Create from HuggingFace dataset row."""
        return cls(
            instance_id=d["instance_id"],
            repo=d["repo"],
            base_commit=d["base_commit"],
            problem_statement=d["problem_statement"],
            hints_text=d.get("hints_text", ""),
            test_patch=d.get("test_patch", ""),
            patch=d.get("patch", ""),
            version=d.get("version", ""),
            environment_setup_commit=d.get("environment_setup_commit", ""),
            metadata={
                "created_at": d.get("created_at"),
                "FAIL_TO_PASS": d.get("FAIL_TO_PASS", ""),
                "PASS_TO_PASS": d.get("PASS_TO_PASS", ""),
            },
        )


def load_swebench(
    split: str = "verified",
    max_tasks: Optional[int] = None,
    instance_ids: Optional[List[str]] = None,
) -> List[SWEBenchTask]:
    """
    Load SWE-bench dataset.

    Args:
        split: Dataset split - "lite", "verified", or "full"
        max_tasks: Maximum tasks to load (None = all)
        instance_ids: Specific instance IDs to load

    Returns:
        List of SWEBenchTask objects
    """
    try:
        from datasets import load_dataset
    except ImportError:
        raise ImportError(
            "Please install datasets: pip install datasets"
        )

    # Map split names to HuggingFace dataset names
    dataset_map = {
        "lite": "princeton-nlp/SWE-bench_Lite",
        "verified": "princeton-nlp/SWE-bench_Verified",
        "full": "princeton-nlp/SWE-bench",
    }

    dataset_name = dataset_map.get(split.lower())
    if not dataset_name:
        raise ValueError(f"Unknown split: {split}. Use: lite, verified, full")

    print(f"Loading {dataset_name}...")
    ds = load_dataset(dataset_name, split="test")

    tasks = []
    for i, row in enumerate(ds):
        # Filter by instance_ids if provided
        if instance_ids and row["instance_id"] not in instance_ids:
            continue

        tasks.append(SWEBenchTask.from_dict(row))

        if max_tasks and len(tasks) >= max_tasks:
            break

    print(f"Loaded {len(tasks)} tasks")
    return tasks


def load_single_task(instance_id: str) -> Optional[SWEBenchTask]:
    """Load a single task by instance ID."""
    # Try each split
    for split in ["verified", "lite", "full"]:
        try:
            tasks = load_swebench(split, instance_ids=[instance_id])
            if tasks:
                return tasks[0]
        except Exception:
            continue
    return None


def iter_swebench(
    split: str = "verified",
    max_tasks: Optional[int] = None,
) -> Iterator[SWEBenchTask]:
    """
    Iterate over SWE-bench tasks (memory efficient).

    Yields tasks one at a time instead of loading all into memory.
    """
    try:
        from datasets import load_dataset
    except ImportError:
        raise ImportError("Please install datasets: pip install datasets")

    dataset_map = {
        "lite": "princeton-nlp/SWE-bench_Lite",
        "verified": "princeton-nlp/SWE-bench_Verified",
        "full": "princeton-nlp/SWE-bench",
    }

    dataset_name = dataset_map.get(split.lower())
    if not dataset_name:
        raise ValueError(f"Unknown split: {split}")

    ds = load_dataset(dataset_name, split="test", streaming=True)

    count = 0
    for row in ds:
        yield SWEBenchTask.from_dict(row)
        count += 1
        if max_tasks and count >= max_tasks:
            break
