#!/usr/bin/env python3
"""
Comprehensive LLM Benchmark Tool

Features:
- Speed benchmarking (tokens/sec, latency percentiles)
- Quality metrics (perplexity, coherence, diversity, repetition)
- Consistency testing (same prompt, multiple runs)
- Unified report format (text, JSON, HTML)
- Multi-engine comparison
"""

import sys
import os
import time
import json
import argparse
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

import psutil
import numpy as np

# Try importing torch for attention mask handling
try:
    import torch
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False

# Add project root to path
try:
    from tools._path_setup import ensure_project_root_on_path
except ImportError:
    from _path_setup import ensure_project_root_on_path

ensure_project_root_on_path()

from src.engines.engine_factory import get_engine
from src.core.model_validator import ModelValidator, print_validation_result
from src.benchmarks.framework.quality_metrics import (
    QualityAnalyzer,
    QualityMetrics,
    BenchmarkReport,
    compute_perplexity
)


# Default test prompts for different scenarios
DEFAULT_PROMPTS = {
    "general": [
        "The quick brown fox jumps over the lazy dog.",
        "In the beginning, there was nothing but potential.",
        "Artificial intelligence is transforming the way we",
    ],
    "coding": [
        "def fibonacci(n):",
        "# Function to calculate the factorial of a number",
        "class DataProcessor:",
    ],
    "creative": [
        "Once upon a time in a kingdom far away,",
        "The sunset painted the sky in shades of",
        "She opened the mysterious letter and read:",
    ],
    "qa": [
        "What is the capital of France?",
        "Explain how photosynthesis works.",
        "What are the benefits of exercise?",
    ]
}


def run_comprehensive_benchmark(
    engine_name: str,
    model_name: str,
    prompts: List[str],
    num_tokens: int = 50,
    iterations: int = 3,
    consistency_runs: int = 3,
    temperature: float = 0.7,
    top_k: int = 50,
    top_p: float = 0.9,
    verbose: bool = False
) -> Dict[str, Any]:
    """
    Run comprehensive benchmark on a single model.

    Returns:
        Dictionary with all benchmark results including quality metrics
    """
    results = {
        "model": model_name,
        "engine": engine_name,
        "config": {
            "num_tokens": num_tokens,
            "iterations": iterations,
            "consistency_runs": consistency_runs,
            "temperature": temperature,
            "top_k": top_k,
            "top_p": top_p,
        },
        "metrics": {},
        "quality": None,
        "outputs": [],
        "errors": []
    }

    # Memory tracking
    process = psutil.Process()
    ram_before = process.memory_info().rss / (1024 * 1024)

    # Load engine
    try:
        engine_config = {
            "temperature": temperature,
            "top_k": top_k,
            "top_p": top_p,
            "use_kv_cache": False,  # Disable KV cache for more reliable benchmarking
            "mode": "benchmark",
        }
        engine = get_engine(engine_name, model_name, engine_config)
        print("Loading model...")
        engine.load()
        print("✓ Model loaded")
    except Exception as e:
        results["errors"].append(f"Failed to load model: {e}")
        return results

    ram_after = process.memory_info().rss / (1024 * 1024)
    results["metrics"]["ram_used_mb"] = ram_after - ram_before
    results["metrics"]["ram_used_gb"] = (ram_after - ram_before) / 1024

    # Initialize quality analyzer
    analyzer = QualityAnalyzer()

    all_latencies = []
    all_tokens_per_sec = []
    all_token_probs = []
    logits_for_perplexity = []
    tokens_for_perplexity = []

    # Run speed benchmark iterations
    print(f"\nRunning {iterations} speed benchmark iterations...")
    for i in range(iterations):
        prompt = prompts[i % len(prompts)]

        try:
            # Reset KV cache for clean run
            if hasattr(engine, 'reset_kv_cache'):
                engine.reset_kv_cache()

            input_ids, attention_mask = engine.encode(prompt)

            iteration_latencies = []
            iteration_tokens = []
            iteration_probs = []
            start_time = time.time()

            # Track generated text for re-encoding approach
            generated_text = prompt

            for step in range(num_tokens):
                step_start = time.time()

                output = engine.predict_next(
                    input_ids,
                    attention_mask,
                    temperature=temperature,
                    top_k=top_k,
                    top_p=top_p
                )

                step_latency = (time.time() - step_start) * 1000  # ms
                iteration_latencies.append(step_latency)

                token_id = output["next_token_id"]
                iteration_tokens.append(token_id)

                # Get token probability for quality metrics
                if "probabilities_processed" in output:
                    probs = output["probabilities_processed"]
                    try:
                        # Handle PyTorch tensors on MPS/CUDA
                        if hasattr(probs, 'cpu'):
                            probs = probs.cpu()
                        if hasattr(probs, 'detach'):
                            probs = probs.detach()
                        if hasattr(probs, 'numpy'):
                            probs_np = probs.numpy().flatten()
                        else:
                            probs_np = np.array(probs).flatten()

                        if 0 <= token_id < len(probs_np):
                            prob = float(probs_np[token_id])
                            iteration_probs.append(prob)
                            all_token_probs.append(prob)
                    except Exception:
                        pass  # Skip if conversion fails

                # Store logits for perplexity
                if "logits_raw" in output:
                    try:
                        logits = output["logits_raw"]
                        if hasattr(logits, 'cpu'):
                            logits = logits.cpu()
                        if hasattr(logits, 'detach'):
                            logits = logits.detach()
                        if hasattr(logits, 'numpy'):
                            logits_np = logits.numpy().flatten()
                        else:
                            logits_np = np.array(logits).flatten()
                        logits_for_perplexity.append(logits_np)
                        tokens_for_perplexity.append(token_id)
                    except Exception:
                        pass  # Skip if conversion fails

                # Check for EOS
                eos_id = engine.get_eos_token_id() if hasattr(engine, 'get_eos_token_id') else None
                if eos_id is not None and token_id == eos_id:
                    break

                # Append token for next iteration - try append_to_input first, fallback to re-encoding
                try:
                    input_ids = engine.append_to_input(input_ids, token_id)
                    # Also extend attention mask to match new input_ids length
                    if attention_mask is not None:
                        if HAS_TORCH and isinstance(attention_mask, torch.Tensor):
                            ones = torch.ones((1, 1), dtype=attention_mask.dtype, device=attention_mask.device)
                            attention_mask = torch.cat([attention_mask, ones], dim=-1)
                        elif hasattr(attention_mask, 'ndim'):  # numpy-like or MLX
                            ones = np.ones((1, 1), dtype=np.int32)
                            attention_mask = np.concatenate([np.array(attention_mask), ones], axis=-1)
                            # Convert back to MLX if needed
                            if 'mlx' in str(type(input_ids)):
                                try:
                                    import mlx.core as mx
                                    attention_mask = mx.array(attention_mask)
                                except ImportError:
                                    pass
                except Exception:
                    # Fallback: decode token and re-encode full sequence
                    try:
                        token_text = engine.decode([token_id], skip_special_tokens=False)
                        generated_text += token_text
                        input_ids, attention_mask = engine.encode(generated_text, add_special_tokens=True)
                    except Exception:
                        break  # Give up if re-encoding also fails

            total_time = time.time() - start_time
            tokens_generated = len(iteration_tokens)
            tps = tokens_generated / total_time if total_time > 0 else 0

            all_latencies.extend(iteration_latencies)
            all_tokens_per_sec.append(tps)

            # Decode and store output
            output_text = engine.decode(iteration_tokens, skip_special_tokens=True)
            results["outputs"].append(output_text)
            analyzer.record_output(output_text, iteration_tokens)

            if verbose:
                print(f"  Iteration {i+1}: {tokens_generated} tokens, {tps:.2f} tok/s")

        except Exception as e:
            results["errors"].append(f"Iteration {i+1} failed: {e}")
            if verbose:
                print(f"  Iteration {i+1}: ERROR - {e}")

    # Run consistency tests (same prompt, multiple runs)
    if consistency_runs > 1:
        print(f"\nRunning {consistency_runs} consistency tests...")
        consistency_prompt = prompts[0]
        consistency_outputs = []

        for run in range(consistency_runs):
            try:
                # Reset KV cache for clean run
                if hasattr(engine, 'reset_kv_cache'):
                    engine.reset_kv_cache()

                input_ids, attention_mask = engine.encode(consistency_prompt)
                run_tokens = []
                generated_text = consistency_prompt

                for _ in range(min(20, num_tokens)):  # Shorter for consistency test
                    try:
                        output = engine.predict_next(
                            input_ids,
                            attention_mask,
                            temperature=0.0,  # Deterministic for consistency test
                            top_k=1,
                            top_p=1.0
                        )
                        token_id = output["next_token_id"]
                        run_tokens.append(token_id)

                        # Try append, fallback to re-encode
                        try:
                            input_ids = engine.append_to_input(input_ids, token_id)
                            # Extend attention mask
                            if attention_mask is not None:
                                if HAS_TORCH and isinstance(attention_mask, torch.Tensor):
                                    ones = torch.ones((1, 1), dtype=attention_mask.dtype, device=attention_mask.device)
                                    attention_mask = torch.cat([attention_mask, ones], dim=-1)
                        except Exception:
                            token_text = engine.decode([token_id], skip_special_tokens=False)
                            generated_text += token_text
                            input_ids, attention_mask = engine.encode(generated_text, add_special_tokens=True)
                    except Exception:
                        break  # Break on errors

                if run_tokens:
                    output_text = engine.decode(run_tokens, skip_special_tokens=True)
                    consistency_outputs.append(output_text)
                    analyzer.record_output(output_text, run_tokens)

            except Exception as e:
                results["errors"].append(f"Consistency run {run+1} failed: {e}")

    # Record latencies for percentile calculation
    for lat in all_latencies:
        analyzer.record_latency(lat)

    # Record token probabilities
    for prob in all_token_probs:
        analyzer.record_token_prob(prob)

    # Compute quality metrics
    quality_metrics = analyzer.compute_metrics()

    # Compute perplexity if we have logits
    if logits_for_perplexity and tokens_for_perplexity:
        quality_metrics.perplexity = compute_perplexity(logits_for_perplexity, tokens_for_perplexity)

    results["quality"] = quality_metrics

    # Aggregate speed metrics
    if all_tokens_per_sec:
        results["metrics"]["tokens_per_second_mean"] = float(np.mean(all_tokens_per_sec))
        results["metrics"]["tokens_per_second_std"] = float(np.std(all_tokens_per_sec))
        results["metrics"]["tokens_per_second_min"] = float(np.min(all_tokens_per_sec))
        results["metrics"]["tokens_per_second_max"] = float(np.max(all_tokens_per_sec))

    if all_latencies:
        results["metrics"]["latency_ms_mean"] = float(np.mean(all_latencies))
        results["metrics"]["latency_ms_std"] = float(np.std(all_latencies))
        results["metrics"]["latency_ms_p50"] = float(np.percentile(all_latencies, 50))
        results["metrics"]["latency_ms_p95"] = float(np.percentile(all_latencies, 95))
        results["metrics"]["latency_ms_p99"] = float(np.percentile(all_latencies, 99))

    results["metrics"]["total_tokens_generated"] = sum(len(o) for o in results["outputs"])
    results["metrics"]["success_rate"] = 1.0 - (len(results["errors"]) / max(iterations, 1))

    return results


def print_results(results: Dict[str, Any], width: int = 80):
    """Print formatted results for a single model."""
    sep = "=" * width

    print(f"\n{sep}")
    print(f" Results: {results['model']} ({results['engine']})")
    print(sep)

    # Speed metrics
    print("\n📊 SPEED METRICS")
    print("-" * 40)
    metrics = results["metrics"]
    if "tokens_per_second_mean" in metrics:
        print(f"  Tokens/sec:     {metrics['tokens_per_second_mean']:.2f} (±{metrics.get('tokens_per_second_std', 0):.2f})")
    if "latency_ms_mean" in metrics:
        print(f"  Latency (mean): {metrics['latency_ms_mean']:.2f}ms")
    if "latency_ms_p50" in metrics:
        print(f"  Latency (p50):  {metrics['latency_ms_p50']:.2f}ms")
    if "latency_ms_p95" in metrics:
        print(f"  Latency (p95):  {metrics['latency_ms_p95']:.2f}ms")
    if "latency_ms_p99" in metrics:
        print(f"  Latency (p99):  {metrics['latency_ms_p99']:.2f}ms")

    # Quality metrics
    quality = results.get("quality")
    if quality:
        print("\n📈 QUALITY METRICS")
        print("-" * 40)
        if quality.perplexity is not None:
            print(f"  Perplexity:     {quality.perplexity:.2f}")
        if quality.coherence_score is not None:
            print(f"  Coherence:      {quality.coherence_score:.2%}")
        if quality.diversity_score is not None:
            print(f"  Diversity:      {quality.diversity_score:.2%}")
        if quality.repetition_ratio is not None:
            print(f"  Repetition:     {quality.repetition_ratio:.2%}")
        if quality.output_consistency is not None:
            print(f"  Consistency:    {quality.output_consistency:.2%}")
        if quality.avg_confidence is not None:
            print(f"  Avg Confidence: {quality.avg_confidence:.2%}")

    # Memory
    print("\n💾 MEMORY")
    print("-" * 40)
    if "ram_used_gb" in metrics:
        print(f"  RAM Used:       {metrics['ram_used_gb']:.2f} GB")

    # Errors
    if results["errors"]:
        print("\n⚠️  ERRORS")
        print("-" * 40)
        for error in results["errors"][:5]:
            print(f"  • {error}")

    print(f"\n{sep}\n")


def print_comparison(all_results: List[Dict[str, Any]], width: int = 80):
    """Print comparison table for multiple models."""
    if len(all_results) < 2:
        return

    sep = "=" * width

    print(f"\n{sep}")
    print(" MODEL COMPARISON".center(width))
    print(sep)

    # Header
    print(f"\n{'Model':<35} {'Engine':<10} {'Tok/s':>8} {'p50':>8} {'p95':>8} {'Quality':>8}")
    print("-" * width)

    # Sort by speed
    sorted_results = sorted(
        all_results,
        key=lambda r: r["metrics"].get("tokens_per_second_mean", 0),
        reverse=True
    )

    for r in sorted_results:
        name = r["model"]
        if len(name) > 33:
            name = name[:30] + "..."
        engine = r["engine"][:8]
        tps = r["metrics"].get("tokens_per_second_mean", 0)
        p50 = r["metrics"].get("latency_ms_p50", 0)
        p95 = r["metrics"].get("latency_ms_p95", 0)

        quality_str = "-"
        if r.get("quality"):
            q = r["quality"]
            if q.coherence_score is not None:
                quality_str = f"{q.coherence_score:.0%}"

        print(f"{name:<35} {engine:<10} {tps:>8.2f} {p50:>7.1f}ms {p95:>7.1f}ms {quality_str:>8}")

    # Winner
    if sorted_results:
        fastest = sorted_results[0]
        print(f"\n🏆 Fastest: {fastest['model']} ({fastest['metrics'].get('tokens_per_second_mean', 0):.2f} tok/s)")

        if len(sorted_results) > 1:
            for i, r in enumerate(sorted_results[1:], 1):
                speedup = fastest["metrics"].get("tokens_per_second_mean", 1) / max(r["metrics"].get("tokens_per_second_mean", 1), 0.001)
                print(f"   {speedup:.2f}x faster than {r['model']}")

    print(f"\n{sep}\n")


def generate_report(
    all_results: List[Dict[str, Any]],
    output_dir: str,
    format: str = "all"
) -> str:
    """Generate and save benchmark report."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_filename = f"benchmark_report_{timestamp}"

    # Create unified report
    report = BenchmarkReport(
        title="Comprehensive LLM Benchmark",
        timestamp=datetime.now().isoformat(),
        summary={
            "models_tested": len(all_results),
            "total_errors": sum(len(r["errors"]) for r in all_results),
        }
    )

    for r in all_results:
        report.add_model_result(
            name=r["model"],
            engine=r["engine"],
            metrics=r["metrics"],
            quality=r.get("quality")
        )

    report.generate_comparison()

    saved_files = []

    # Save JSON
    if format in ("json", "all"):
        json_path = output_path / f"{base_filename}.json"
        with open(json_path, 'w') as f:
            # Convert quality metrics for JSON serialization
            json_data = {
                "report": report.to_dict(),
                "raw_results": [
                    {**r, "quality": r["quality"].to_dict() if r.get("quality") else None}
                    for r in all_results
                ]
            }
            json.dump(json_data, f, indent=2, default=str)
        saved_files.append(str(json_path))

    # Save text report
    if format in ("text", "all"):
        text_path = output_path / f"{base_filename}.txt"
        with open(text_path, 'w') as f:
            f.write(report.to_text())
        saved_files.append(str(text_path))

    return ", ".join(saved_files)


def main():
    parser = argparse.ArgumentParser(
        description="Comprehensive LLM Benchmark Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic comparison
  %(prog)s --models pytorch:google/gemma-2b mlx:mlx-community/gemma-2-2b-it-4bit

  # Full benchmark with quality metrics
  %(prog)s --models pytorch:google/gemma-2b \\
           --tokens 100 --iterations 5 --consistency-runs 3

  # Save reports
  %(prog)s --models pytorch:google/gemma-2b --save --output ./results

  # Use specific prompts
  %(prog)s --models pytorch:google/gemma-2b --prompt-type coding

Supported engines:
  pytorch, mlx, llamacpp, ollama, vllm, tensorflow, jax, onnx
        """
    )

    parser.add_argument("--models", nargs="+", required=True, metavar="ENGINE:MODEL",
                        help="Models to benchmark (engine:model format)")
    parser.add_argument("--tokens", type=int, default=50,
                        help="Tokens to generate per iteration (default: 50)")
    parser.add_argument("--iterations", type=int, default=3,
                        help="Number of benchmark iterations (default: 3)")
    parser.add_argument("--consistency-runs", type=int, default=3,
                        help="Runs for consistency testing (default: 3)")
    parser.add_argument("--temperature", type=float, default=0.7,
                        help="Sampling temperature (default: 0.7)")
    parser.add_argument("--top-k", type=int, default=50,
                        help="Top-K sampling (default: 50)")
    parser.add_argument("--top-p", type=float, default=0.9,
                        help="Top-P sampling (default: 0.9)")
    parser.add_argument("--prompt-type", choices=["general", "coding", "creative", "qa"],
                        default="general", help="Type of test prompts (default: general)")
    parser.add_argument("--prompts", nargs="+", help="Custom prompts (overrides --prompt-type)")
    parser.add_argument("--save", action="store_true", help="Save report to file")
    parser.add_argument("--output", default="./output/benchmarks",
                        help="Output directory for reports (default: ./output/benchmarks)")
    parser.add_argument("--format", choices=["json", "text", "all"], default="all",
                        help="Report format (default: all)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--list-models", action="store_true", help="List available models")

    args = parser.parse_args()

    if args.list_models:
        print("\nAvailable Models:\n")
        # HuggingFace cache
        hf_cache = os.path.expanduser("~/.cache/huggingface/hub")
        if os.path.exists(hf_cache):
            cached = [d for d in os.listdir(hf_cache) if d.startswith('models--')]
            print("HuggingFace cached:")
            for m in sorted(cached)[:10]:
                model_name = m.replace('models--', '').replace('__', '/')
                print(f"  pytorch:{model_name}")
        return 0

    # Get prompts
    prompts = args.prompts if args.prompts else DEFAULT_PROMPTS[args.prompt_type]

    # Validate models
    print("\n" + "=" * 70)
    print("Validating model specifications...")
    print("=" * 70)

    valid_models = []
    for model_spec in args.models:
        if ":" not in model_spec:
            model_spec = f"pytorch:{model_spec}"

        validation = ModelValidator.validate_model_spec(model_spec, require_logits=False)
        if not print_validation_result(validation, model_spec):
            print(f"⚠️  Skipping: {model_spec}\n")
            continue
        valid_models.append(model_spec)

    if not valid_models:
        print("\n❌ No valid models to benchmark.")
        return 1

    print(f"\n✓ Validated {len(valid_models)} model(s)\n")

    # Run benchmarks
    all_results = []

    for model_spec in valid_models:
        engine_name, model_name = model_spec.split(":", 1)

        print("\n" + "=" * 70)
        print(f"Benchmarking: {model_name} ({engine_name})")
        print("=" * 70)

        result = run_comprehensive_benchmark(
            engine_name=engine_name,
            model_name=model_name,
            prompts=prompts,
            num_tokens=args.tokens,
            iterations=args.iterations,
            consistency_runs=args.consistency_runs,
            temperature=args.temperature,
            top_k=args.top_k,
            top_p=args.top_p,
            verbose=args.verbose
        )

        all_results.append(result)
        print_results(result)

    # Print comparison
    if len(all_results) > 1:
        print_comparison(all_results)

    # Save reports
    if args.save:
        saved = generate_report(all_results, args.output, args.format)
        print(f"📄 Reports saved: {saved}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
