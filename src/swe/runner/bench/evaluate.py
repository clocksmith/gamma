"""
SWE-bench evaluation - calls official harness.

After generating predictions.jsonl, this runs the official
SWE-bench evaluation to get pass@1 scores.
"""

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class EvalResult:
    """Result of SWE-bench evaluation."""
    total: int = 0
    resolved: int = 0
    unresolved: int = 0
    error: int = 0
    pass_rate: float = 0.0
    details: Dict[str, str] = None  # instance_id -> status

    def __post_init__(self):
        if self.details is None:
            self.details = {}


def evaluate_predictions(
    predictions_path: str,
    dataset: str = "princeton-nlp/SWE-bench_Verified",
    max_workers: int = 4,
    timeout: int = 1800,
    output_dir: Optional[str] = None,
) -> EvalResult:
    """
    Evaluate predictions using official SWE-bench harness.

    Requires: pip install swebench

    Args:
        predictions_path: Path to predictions.jsonl
        dataset: Dataset name
        max_workers: Parallel workers for evaluation
        timeout: Timeout per instance (seconds)
        output_dir: Directory for evaluation logs

    Returns:
        EvalResult with pass rates
    """
    predictions_path = Path(predictions_path)
    if not predictions_path.exists():
        raise FileNotFoundError(f"Predictions not found: {predictions_path}")

    output_dir = Path(output_dir or predictions_path.parent / "eval_results")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Try to import swebench
    try:
        from swebench.harness.run_evaluation import main as run_evaluation
        use_python_api = True
    except ImportError:
        use_python_api = False
        print("swebench not installed, trying CLI...")

    if use_python_api:
        # Use Python API
        return _evaluate_python_api(
            predictions_path,
            dataset,
            max_workers,
            timeout,
            output_dir,
        )
    else:
        # Fall back to CLI
        return _evaluate_cli(
            predictions_path,
            dataset,
            max_workers,
            timeout,
            output_dir,
        )


def _evaluate_python_api(
    predictions_path: Path,
    dataset: str,
    max_workers: int,
    timeout: int,
    output_dir: Path,
) -> EvalResult:
    """Evaluate using swebench Python API."""
    from swebench.harness.run_evaluation import main as run_evaluation

    # Run evaluation
    run_evaluation(
        dataset_name=dataset,
        predictions_path=str(predictions_path),
        max_workers=max_workers,
        timeout=timeout,
        run_id=output_dir.name,
        output_dir=str(output_dir),
    )

    # Parse results
    return _parse_results(output_dir)


def _evaluate_cli(
    predictions_path: Path,
    dataset: str,
    max_workers: int,
    timeout: int,
    output_dir: Path,
) -> EvalResult:
    """Evaluate using swebench CLI."""
    cmd = [
        "python", "-m", "swebench.harness.run_evaluation",
        "--dataset_name", dataset,
        "--predictions_path", str(predictions_path),
        "--max_workers", str(max_workers),
        "--timeout", str(timeout),
        "--output_dir", str(output_dir),
    ]

    print(f"Running: {' '.join(cmd)}")

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout * 10,  # Overall timeout
        )

        if result.returncode != 0:
            print(f"Evaluation failed: {result.stderr}")
            return EvalResult(error=1)

    except subprocess.TimeoutExpired:
        print("Evaluation timed out")
        return EvalResult(error=1)
    except FileNotFoundError:
        print("swebench CLI not found. Install with: pip install swebench")
        return EvalResult(error=1)

    return _parse_results(output_dir)


def _parse_results(output_dir: Path) -> EvalResult:
    """Parse evaluation results from output directory."""
    result = EvalResult()

    # Look for results file
    results_file = output_dir / "results.json"
    if not results_file.exists():
        # Try alternative locations
        for f in output_dir.glob("**/results.json"):
            results_file = f
            break

    if results_file.exists():
        with open(results_file) as f:
            data = json.load(f)

        result.total = data.get("total", 0)
        result.resolved = data.get("resolved", 0)
        result.unresolved = result.total - result.resolved
        result.pass_rate = result.resolved / result.total if result.total > 0 else 0.0

        # Get per-instance results
        if "per_instance" in data:
            result.details = data["per_instance"]

    # Also check for report.json
    report_file = output_dir / "report.json"
    if report_file.exists():
        with open(report_file) as f:
            report = json.load(f)

        if "resolved" in report:
            result.resolved = len(report["resolved"])
        if "unresolved" in report:
            result.unresolved = len(report["unresolved"])

        result.total = result.resolved + result.unresolved
        result.pass_rate = result.resolved / result.total if result.total > 0 else 0.0

    return result


def quick_eval(predictions_path: str) -> None:
    """
    Quick evaluation with nice output.

    Usage:
        python -c "from gamma.src.swe.runner.bench import quick_eval; quick_eval('predictions.jsonl')"
    """
    print(f"Evaluating {predictions_path}...")
    result = evaluate_predictions(predictions_path)

    print("\n" + "="*50)
    print("SWE-bench Evaluation Results")
    print("="*50)
    print(f"Total:      {result.total}")
    print(f"Resolved:   {result.resolved}")
    print(f"Unresolved: {result.unresolved}")
    print(f"Pass Rate:  {result.pass_rate*100:.1f}%")
    print("="*50)
