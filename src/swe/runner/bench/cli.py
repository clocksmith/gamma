#!/usr/bin/env python3
"""
CLI for running SWE-bench evaluations.

Usage:
    # Run on SWE-bench Verified (mock models for testing)
    python -m gamma.src.swe.runner.bench.cli --mock --max-tasks 5

    # Run on specific instances
    python -m gamma.src.swe.runner.bench.cli --mock --instances django__django-11099

    # Run with real models (requires setup)
    python -m gamma.src.swe.runner.bench.cli --conductor ollama:llama3.1:70b

    # Just evaluate existing predictions
    python -m gamma.src.swe.runner.bench.cli --eval-only predictions.jsonl
"""

import argparse
import asyncio
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(
        description="Run SWE-bench evaluation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Quick test with mock models
    python -m gamma.src.swe.runner.bench.cli --mock --max-tasks 3

    # Run on SWE-bench Lite
    python -m gamma.src.swe.runner.bench.cli --mock --split lite --max-tasks 10

    # Run specific instance
    python -m gamma.src.swe.runner.bench.cli --mock --instances django__django-11099

    # Evaluate existing predictions
    python -m gamma.src.swe.runner.bench.cli --eval-only predictions.jsonl
        """,
    )

    # Mode
    parser.add_argument(
        "--mock", action="store_true",
        help="Use mock models (for testing)"
    )
    parser.add_argument(
        "--eval-only", metavar="FILE",
        help="Only evaluate existing predictions file"
    )

    # Dataset
    parser.add_argument(
        "--split", default="verified",
        choices=["lite", "verified", "full"],
        help="SWE-bench split (default: verified)"
    )
    parser.add_argument(
        "--max-tasks", type=int,
        help="Maximum tasks to run"
    )
    parser.add_argument(
        "--instances", nargs="+",
        help="Specific instance IDs to run"
    )

    # Output
    parser.add_argument(
        "-o", "--output", default="predictions.jsonl",
        help="Output predictions file"
    )
    parser.add_argument(
        "--output-dir", default="./swe-bench-results",
        help="Output directory for results"
    )

    # Execution
    parser.add_argument(
        "--parallel", type=int, default=1,
        help="Parallel tasks (default: 1)"
    )
    parser.add_argument(
        "--cost-limit", type=float, default=10.0,
        help="Cost limit per task"
    )
    parser.add_argument(
        "--require-tests-pass", action="store_true",
        help="Fail task if tests do not pass"
    )
    parser.add_argument(
        "--fail-on-test-error", action="store_true",
        help="Fail task if test runner errors"
    )

    # Models (for real runs)
    parser.add_argument(
        "--conductor", default="ollama:gptoss-20b",
        help="Conductor model (format: provider:model)"
    )
    parser.add_argument(
        "--fng-model", default="ollama:functiongemma",
        help="FunctionGemma model"
    )
    parser.add_argument(
        "--ring-nodes", type=int, default=4,
        help="Number of FnG ring nodes"
    )

    args = parser.parse_args()

    # Eval-only mode
    if args.eval_only:
        from .evaluate import quick_eval
        quick_eval(args.eval_only)
        return 0

    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Create agent
    if args.mock:
        from ...agent import create_agent_mock, AgentConfig
        config = AgentConfig(
            cost_limit=args.cost_limit,
            output_dir=str(output_dir / "trajectories"),
        )
        agent = create_agent_mock(config)
        print("Using mock models for testing")
    else:
        # Real models
        agent = create_real_agent(args)
        if agent is None:
            return 1

    # Run
    from .runner import SWEBenchRunner

    async def run():
        runner = SWEBenchRunner(
            agent,
            work_dir=str(output_dir / "repos"),
            require_tests_pass=args.require_tests_pass,
            fail_on_test_error=args.fail_on_test_error,
        )

        result = await runner.run(
            split=args.split,
            max_tasks=args.max_tasks,
            instance_ids=args.instances,
            parallel=args.parallel,
        )

        # Save predictions
        predictions_path = output_dir / args.output
        runner.save_predictions(str(predictions_path))

        # Auto-evaluate if swebench is installed
        try:
            from .evaluate import evaluate_predictions
            print("\nRunning evaluation...")
            eval_result = evaluate_predictions(
                str(predictions_path),
                output_dir=str(output_dir / "eval"),
            )
            print(f"\nPass Rate: {eval_result.pass_rate*100:.1f}%")
            print(f"Resolved: {eval_result.resolved}/{eval_result.total}")
        except Exception as e:
            print(f"\nSkipping evaluation: {e}")
            print(f"Run manually: python -m swebench.harness.run_evaluation "
                  f"--predictions_path {predictions_path}")

        return result

    result = asyncio.run(run())

    return 0


def create_real_agent(args):
    """Create agent with real models."""
    import asyncio

    provider, model = args.conductor.split(":", 1) if ":" in args.conductor else ("ollama", args.conductor)

    if provider == "ollama":
        print(f"Creating Ollama agent with conductor={model}")
        try:
            from ..integrations.ollama import create_ollama_agent, check_ollama_available

            # Check if Ollama is running
            if not asyncio.run(check_ollama_available()):
                print("Error: Ollama server not running")
                print("Start Ollama with: ollama serve")
                print("Or use --mock for testing")
                return None

            return asyncio.run(create_ollama_agent(
                conductor_model=model,
                fng_model=args.fng_model.split(":", 1)[-1],
                num_nodes=args.ring_nodes,
            ))
        except ImportError as e:
            print(f"Ollama integration error: {e}")
            print("Install httpx: pip install httpx")
            return None

    elif provider == "anthropic":
        print(f"Creating Anthropic agent with conductor={model}")
        try:
            from ..integrations.anthropic import create_anthropic_agent
            import os

            if not os.environ.get("ANTHROPIC_API_KEY"):
                print("Error: ANTHROPIC_API_KEY not set")
                print("export ANTHROPIC_API_KEY='sk-...'")
                return None

            return asyncio.run(create_anthropic_agent(
                conductor_model=model,
                fng_model=args.fng_model,
                num_nodes=args.ring_nodes,
            ))
        except ImportError as e:
            print(f"Anthropic integration error: {e}")
            print("Install anthropic: pip install anthropic")
            return None
        except ValueError as e:
            print(f"Configuration error: {e}")
            return None

    else:
        print(f"Unknown provider: {provider}")
        print("Supported: ollama, anthropic")
        return None



if __name__ == "__main__":
    sys.exit(main())
