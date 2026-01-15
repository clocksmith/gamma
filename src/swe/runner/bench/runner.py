"""
SWE-bench runner - orchestrates full evaluation.

For each task:
1. Clone repo at base_commit
2. Run agent to generate patch
3. Save prediction
"""

import asyncio
import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from .dataset import SWEBenchTask, load_swebench
from ...agent import SWEAgentV2, AgentConfig
from ..execution.git_tools import GitTools, ApplyStatus
from ..execution.test_runner import TestRunner


@dataclass
class Prediction:
    """Single prediction for SWE-bench."""
    instance_id: str
    model_patch: str
    model_name_or_path: str = "gamma-swe-agent-v2"

    # Metadata
    duration_seconds: float = 0.0
    exit_status: str = ""
    error: Optional[str] = None
    test_status: Optional[str] = None
    test_summary: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "instance_id": self.instance_id,
            "model_patch": self.model_patch,
            "model_name_or_path": self.model_name_or_path,
        }


@dataclass
class RunResult:
    """Result of running on SWE-bench."""
    predictions: List[Prediction] = field(default_factory=list)
    total_tasks: int = 0
    completed: int = 0
    failed: int = 0
    duration_seconds: float = 0.0


class SWEBenchRunner:
    """
    Runs agent on SWE-bench tasks.

    Usage:
        runner = SWEBenchRunner(agent)
        result = await runner.run(split="verified", max_tasks=10)
        runner.save_predictions("predictions.jsonl")
    """

    def __init__(
        self,
        agent: SWEAgentV2,
        work_dir: str = "/tmp/swe-bench-runs",
        require_tests_pass: bool = False,
        fail_on_test_error: bool = False,
    ):
        self.agent = agent
        self.work_dir = Path(work_dir)
        self.work_dir.mkdir(parents=True, exist_ok=True)
        self.git = GitTools(work_dir=str(self.work_dir))
        self.tester = TestRunner()
        self.predictions: List[Prediction] = []
        self.require_tests_pass = require_tests_pass
        self.fail_on_test_error = fail_on_test_error

    async def run(
        self,
        split: str = "verified",
        max_tasks: Optional[int] = None,
        instance_ids: Optional[List[str]] = None,
        parallel: int = 1,
    ) -> RunResult:
        """
        Run agent on SWE-bench tasks.

        Args:
            split: Dataset split (lite, verified, full)
            max_tasks: Max tasks to run
            instance_ids: Specific tasks to run
            parallel: Number of parallel tasks (1 = sequential)

        Returns:
            RunResult with predictions
        """
        # Load tasks
        tasks = load_swebench(split, max_tasks, instance_ids)

        result = RunResult(total_tasks=len(tasks))
        start_time = time.time()

        if parallel == 1:
            # Sequential
            for i, task in enumerate(tasks):
                print(f"\n[{i+1}/{len(tasks)}] {task.instance_id}")
                pred = await self._run_single(task)
                self.predictions.append(pred)

                if pred.error:
                    result.failed += 1
                else:
                    result.completed += 1
        else:
            # Parallel with semaphore
            sem = asyncio.Semaphore(parallel)

            async def run_with_sem(task: SWEBenchTask) -> Prediction:
                async with sem:
                    return await self._run_single(task)

            preds = await asyncio.gather(*[
                run_with_sem(task) for task in tasks
            ])

            for pred in preds:
                self.predictions.append(pred)
                if pred.error:
                    result.failed += 1
                else:
                    result.completed += 1

        result.predictions = self.predictions
        result.duration_seconds = time.time() - start_time

        print(f"\nCompleted: {result.completed}/{result.total_tasks}")
        print(f"Failed: {result.failed}")
        print(f"Duration: {result.duration_seconds:.1f}s")

        return result

    async def _run_single(self, task: SWEBenchTask) -> Prediction:
        """Run agent on a single task."""
        start_time = time.time()
        error = None
        patch = ""
        exit_status = "Unknown"
        test_status = None
        test_summary = None

        try:
            # Clone repo
            print(f"  Cloning {task.repo}@{task.base_commit[:8]}...")
            clone_result = await self.git.clone(
                task.repo_url,
                task.base_commit,
                dest_name=task.instance_id.replace("/", "_"),
            )

            if not clone_result.success:
                raise RuntimeError(f"Clone failed: {clone_result.message}")

            task.repo_path = clone_result.path

            # Build prompt
            prompt = self._build_prompt(task)

            # Run agent
            print(f"  Running agent...")
            patch = await self.agent.solve(prompt)
            exit_status = "Submitted"

            # Extract patch from response if needed
            patch = self._extract_patch(patch)

            print(f"  Generated patch: {len(patch)} chars")

            # Apply patch
            apply_result = await self.git.apply_patch(patch, task.repo_path)
            if apply_result.status != ApplyStatus.SUCCESS:
                raise RuntimeError(f"Patch apply failed: {apply_result.message}")

            # Run tests
            print("  Running tests...")
            test_result = await self.tester.run(task.repo_path)
            test_status = test_result.status.value
            test_summary = (
                f"passed={test_result.passed} failed={test_result.failed} "
                f"errors={test_result.errors} total={test_result.total}"
            )
            print(f"  Tests: {test_status} ({test_summary})")

            if self.fail_on_test_error and test_result.status == test_result.status.ERROR:
                raise RuntimeError("Test runner error")
            if self.require_tests_pass and not test_result.all_passed:
                raise RuntimeError("Tests did not pass")

        except Exception as e:
            error = str(e)
            exit_status = "Error"
            print(f"  Error: {error}")

        return Prediction(
            instance_id=task.instance_id,
            model_patch=patch,
            duration_seconds=time.time() - start_time,
            exit_status=exit_status,
            error=error,
            test_status=test_status,
            test_summary=test_summary,
        )

    def _build_prompt(self, task: SWEBenchTask) -> str:
        """Build prompt for agent."""
        prompt = f"""Fix the following issue in the {task.repo} repository.

## Issue
{task.problem_statement}

## Repository
- Repo: {task.repo}
- Commit: {task.base_commit}
- Path: {task.repo_path}

"""
        if task.hints_text:
            prompt += f"""## Hints
{task.hints_text}

"""
        prompt += """## Instructions
1. Explore the codebase to understand the issue
2. Find the relevant files and code
3. Write a fix
4. Output your solution as a git diff/patch

When done, output your final patch in this format:
```diff
<your patch here>
```
"""
        return prompt

    def _extract_patch(self, response: str) -> str:
        """Extract patch from agent response."""
        # Try to find diff block
        if "```diff" in response:
            parts = response.split("```diff")
            if len(parts) > 1:
                return parts[1].split("```")[0].strip()

        if "```" in response:
            # Try any code block
            parts = response.split("```")
            if len(parts) > 2:
                return parts[1].strip()

        # Return as-is if no code blocks
        return response.strip()

    def save_predictions(self, path: str) -> None:
        """Save predictions to JSONL file."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w") as f:
            for pred in self.predictions:
                f.write(json.dumps(pred.to_dict()) + "\n")

        print(f"Saved {len(self.predictions)} predictions to {path}")


async def run_swebench(
    agent: SWEAgentV2,
    split: str = "verified",
    max_tasks: Optional[int] = None,
    output: str = "predictions.jsonl",
) -> RunResult:
    """
    Convenience function to run SWE-bench evaluation.

    Args:
        agent: The agent to evaluate
        split: Dataset split
        max_tasks: Max tasks
        output: Output file path

    Returns:
        RunResult
    """
    runner = SWEBenchRunner(agent)
    result = await runner.run(split=split, max_tasks=max_tasks)
    runner.save_predictions(output)
    return result
