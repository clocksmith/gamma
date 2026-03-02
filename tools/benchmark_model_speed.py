#!/usr/bin/env python3
"""
Quick model speed benchmark tool.
Tests tokens per second for different models/engines.
"""

import sys
import os
import time
import argparse
import psutil

# Add project root to path
try:
    from tools._path_setup import ensure_project_root_on_path
except ImportError:
    from _path_setup import ensure_project_root_on_path

ensure_project_root_on_path()

from src.benchmarks.framework.base_benchmark import SpeedBenchmark, BenchmarkConfig
from src.engines.engine_factory import get_engine
from src.core.model_validator import ModelValidator, print_validation_result

def benchmark_model(engine_name: str, model_name: str, num_tokens: int = 50, iterations: int = 3):
    """Benchmark a single model."""

    print(f"\n{'='*70}")
    print(f"Benchmarking: {model_name} ({engine_name})")
    print(f"{'='*70}")

    # Measure RAM before loading
    process = psutil.Process()
    ram_before_mb = process.memory_info().rss / (1024 * 1024)  # Convert to MB

    # Load engine
    try:
        engine = get_engine(engine_name, model_name, {"mode": "benchmark"})
        print("Loading model...")
        engine.load()
        print("✓ Model loaded")

        # Measure RAM after loading
        ram_after_mb = process.memory_info().rss / (1024 * 1024)  # Convert to MB
        ram_used_mb = ram_after_mb - ram_before_mb
        ram_used_gb = ram_used_mb / 1024

    except Exception as e:
        print(f"✗ Failed to load model: {e}")
        return None

    # Create benchmark config
    config = BenchmarkConfig(
        name=f"speed_test_{model_name}",
        description=f"Speed benchmark for {model_name}",
        max_tokens=num_tokens,
        num_iterations=iterations,
        temperature=0.7,
        top_k=50,
        top_p=0.9
    )

    # Test prompts
    prompts = [
        "The quick brown fox",
        "Once upon a time",
        "In the beginning",
        "Artificial intelligence is"
    ]

    # Run benchmark
    benchmark = SpeedBenchmark(config, prompts)
    result = benchmark.run(engine)

    # Add RAM metrics to result
    result.metadata['ram_before_mb'] = ram_before_mb
    result.metadata['ram_after_mb'] = ram_after_mb
    result.metadata['ram_used_mb'] = ram_used_mb
    result.metadata['ram_used_gb'] = ram_used_gb

    # Display results
    print(f"\n{'='*70}")
    print(f"Results for {model_name}")
    print(f"{'='*70}")
    print(f"Tokens per second: {result.metrics.get('tokens_per_second_mean', 0):.2f} tok/s")
    print(f"Latency per token: {result.metrics.get('latency_ms_mean', 0):.2f} ms")
    print(f"Total time: {result.metrics.get('total_time_seconds', 0):.2f} s")
    print(f"Success rate: {result.metadata['success_rate']*100:.1f}%")
    print(f"\nMemory Usage:")
    print(f"  RAM before loading: {ram_before_mb:.1f} MB ({ram_before_mb/1024:.2f} GB)")
    print(f"  RAM after loading:  {ram_after_mb:.1f} MB ({ram_after_mb/1024:.2f} GB)")
    print(f"  RAM used by model:  {ram_used_mb:.1f} MB ({ram_used_gb:.2f} GB)")
    print(f"{'='*70}\n")

    return result


def compare_models(results):
    """Compare multiple model results."""
    if len(results) < 2:
        return

    print(f"\n{'='*70}")
    print("Model Comparison")
    print(f"{'='*70}")

    # Sort by speed
    sorted_results = sorted(
        results,
        key=lambda r: r.metrics.get('tokens_per_second_mean', 0),
        reverse=True
    )

    print(f"\n{'Model':<30} {'Engine':<15} {'Tokens/s':<12} {'Latency (ms)':<15} {'RAM (GB)':<10}")
    print("-" * 80)

    for result in sorted_results:
        tok_per_sec = result.metrics.get('tokens_per_second_mean', 0)
        latency = result.metrics.get('latency_ms_mean', 0)
        ram_gb = result.metadata.get('ram_used_gb', 0)
        print(f"{result.model_name:<30} {result.engine_name:<15} {tok_per_sec:>10.2f}   {latency:>12.2f}   {ram_gb:>8.2f}")

    # Show speedup
    if len(sorted_results) > 1:
        fastest = sorted_results[0]
        print(f"\n{fastest.model_name} is fastest!")

        for i, result in enumerate(sorted_results[1:], 1):
            speedup = fastest.metrics.get('tokens_per_second_mean', 1) / result.metrics.get('tokens_per_second_mean', 1)
            print(f"  {speedup:.2f}x faster than {result.model_name}")

    print(f"{'='*70}\n")


def main():
    parser = argparse.ArgumentParser(
        description="Benchmark model inference speed",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Compare Ollama models (use names from 'ollama list')
  %(prog)s --models ollama:gemma2:2b ollama:qwen2:7b

  # Compare Ollama vs PyTorch/HuggingFace (use HuggingFace repo names)
  %(prog)s --models ollama:gemma2:2b pytorch:google/gemma-2-2b-it

  # Multiple engines
  %(prog)s --models ollama:qwen2:7b pytorch:Qwen/Qwen2-7B-Instruct vllm:Qwen/Qwen2-7B-Instruct

Supported engines:
  ollama       - Use models from 'ollama list' (e.g., ollama:gemma2:2b)
  pytorch      - HuggingFace models (e.g., pytorch:google/gemma-2-2b-it)
  vllm         - Fast inference with vLLM (e.g., vllm:google/gemma-2-2b-it)
  pytorch_cuda - PyTorch with CUDA optimizations
  mlx          - Apple Silicon optimized (e.g., mlx:mlx-community/Llama-3.2-1B-Instruct-4bit)

Model name formats:
  Ollama:      Use exact name from 'ollama list' → ollama:gemma2:2b
  HuggingFace: Use repo format org/model-name → pytorch:google/gemma-2-2b-it
  Local:       Use file path → llamacpp:/path/to/model.gguf
        """
    )

    parser.add_argument(
        "--models",
        nargs="+",
        required=True,
        metavar="ENGINE:MODEL",
        help="Models to benchmark in format engine:model (see examples below)"
    )
    parser.add_argument(
        "--tokens",
        type=int,
        default=50,
        help="Number of tokens to generate per iteration (default: 50)"
    )
    parser.add_argument(
        "--iterations",
        type=int,
        default=3,
        help="Number of iterations per model (default: 3)"
    )
    parser.add_argument(
        "--save",
        action="store_true",
        help="Save results to file"
    )
    parser.add_argument(
        "--list-models",
        action="store_true",
        help="List available models and exit"
    )

    args = parser.parse_args()

    # Handle --list-models
    if args.list_models:
        print("Available Models:\n")

        # List Ollama models
        print("Ollama models (from 'ollama list'):")
        try:
            import subprocess
            result = subprocess.run(['ollama', 'list'], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')[1:]  # Skip header
                for line in lines:
                    parts = line.split()
                    if parts:
                        model_name = parts[0]
                        size = parts[2] if len(parts) > 2 else 'N/A'
                        print(f"  ollama:{model_name:<30} ({size})")
            else:
                print("  (Ollama not available)")
        except Exception as e:
            print(f"  (Error: {e})")

        # List HuggingFace cache
        print("\nHuggingFace cached models:")
        import os
        hf_cache = os.path.expanduser("~/.cache/huggingface/hub")
        if os.path.exists(hf_cache):
            cached = [d for d in os.listdir(hf_cache) if d.startswith('models--')]
            if cached:
                for model_dir in sorted(cached)[:10]:  # Show first 10
                    model_name = model_dir.replace('models--', '').replace('__', '/')
                    print(f"  pytorch:{model_name}")
                if len(cached) > 10:
                    print(f"  ... and {len(cached) - 10} more")
            else:
                print("  (No cached models)")
        else:
            print("  (Cache directory not found)")

        print("\nTo benchmark, use: --models ENGINE:MODEL [ENGINE:MODEL ...]")
        print("Example: --models ollama:gemma2:2b pytorch:google/gemma-2-2b-it")
        return 0

    # Validate all model specifications first
    print("\n" + "="*70)
    print("Validating model specifications...")
    print("="*70)

    valid_models = []
    for model_spec in args.models:
        # Add default engine if not specified
        if ":" not in model_spec:
            model_spec = f"ollama:{model_spec}"

        # Validate the specification
        validation_result = ModelValidator.validate_model_spec(
            model_spec,
            require_logits=False  # Benchmarking doesn't require logits
        )

        if not print_validation_result(validation_result, model_spec):
            print(f"❌ Skipping invalid model: {model_spec}\n")
            continue

        valid_models.append(model_spec)

    if not valid_models:
        print("\n❌ No valid models to benchmark. Exiting.")
        return 1

    print(f"\n✓ Validated {len(valid_models)} model(s)\n")

    results = []

    for model_spec in valid_models:
        # Parse engine:model format
        engine_name, model_name = model_spec.split(":", 1)

        result = benchmark_model(engine_name, model_name, args.tokens, args.iterations)

        if result:
            results.append(result)

            # Save if requested
            if args.save:
                from src.benchmarks.framework.base_benchmark import BaseBenchmark
                benchmark = SpeedBenchmark(
                    BenchmarkConfig(name="speed", description="Speed test"),
                    ["test"]
                )
                benchmark.results = [result]
                benchmark.save_results()

    # Compare results
    if len(results) > 1:
        compare_models(results)

    return 0 if results else 1


if __name__ == "__main__":
    sys.exit(main())
