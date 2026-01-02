#!/usr/bin/env python3
"""
Unified benchmark CLI for comparing inference engines.

Usage:
    bench.py ollama gpt-oss:20b                    # Single Ollama model
    bench.py transformers openai/gpt-oss-20b      # Single HF model
    bench.py vllm openai/gpt-oss-20b              # Single vLLM model

    # Compare engines
    bench.py compare --ollama gpt-oss:20b --hf openai/gpt-oss-20b --vllm openai/gpt-oss-20b

    # With quantization
    bench.py transformers openai/gpt-oss-20b --quant int4
    bench.py vllm openai/gpt-oss-20b --quant awq
"""

import argparse
import json
import sys
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from bench_runners import BenchResult, OllamaRunner, TransformersRunner, VLLMRunner, WebLLMRunner, DopplerRunner


def print_result(result: BenchResult) -> None:
    """Print a single benchmark result."""
    print(f"\n{'='*60}")
    print(f"Results: {result.name} ({result.engine})")
    print(f"{'='*60}")
    print(f"Quantization: {result.quantization}")
    print(f"Tokens/sec:   {result.tokens_per_sec:.2f}")
    print(f"Total tokens: {result.total_tokens}")
    print(f"Total time:   {result.elapsed_sec:.2f}s")

    if result.model_size_gb:
        print(f"Model size:   {result.model_size_gb:.1f} GB")
    if result.vram_gb:
        print(f"VRAM used:    {result.vram_gb:.2f} GB")
    if result.ram_gb:
        print(f"RAM used:     {result.ram_gb:.2f} GB")
    if result.error:
        print(f"Error:        {result.error}")

    # Show sample output for quality validation
    if result.sample_output:
        print(f"\n--- Sample Output (first 300 chars) ---")
        sample = result.sample_output[:300]
        if len(result.sample_output) > 300:
            sample += "..."
        print(sample)
        print(f"--- End Sample ---")

    print(f"{'='*60}")


def print_comparison(results: list[BenchResult]) -> None:
    """Print comparison table."""
    print(f"\n{'='*80}")
    print("COMPARISON RESULTS")
    print(f"{'='*80}\n")

    # Header
    print(f"{'Model':<35} {'Engine':<12} {'Quant':<15} {'Tok/s':>8} {'Mem (GB)':>10}")
    print("-" * 85)

    # Sort by speed
    sorted_results = sorted(results, key=lambda x: x.tokens_per_sec, reverse=True)

    for r in sorted_results:
        mem_str = "N/A"
        if r.vram_gb:
            mem_str = f"{r.vram_gb:.1f} VRAM"
        elif r.model_size_gb:
            mem_str = f"{r.model_size_gb:.1f}"
        elif r.ram_gb:
            mem_str = f"{r.ram_gb:.1f} RAM"

        name = r.name[:33] + ".." if len(r.name) > 35 else r.name
        quant = r.quantization[:13] + ".." if len(r.quantization) > 15 else r.quantization

        print(f"{name:<35} {r.engine:<12} {quant:<15} {r.tokens_per_sec:>8.2f} {mem_str:>10}")

    print("-" * 85)

    # Speedup comparison
    if len(sorted_results) >= 2:
        fastest = sorted_results[0]
        print(f"\nFastest: {fastest.engine} ({fastest.name})")

        for r in sorted_results[1:]:
            if r.tokens_per_sec > 0:
                speedup = fastest.tokens_per_sec / r.tokens_per_sec
                print(f"  {speedup:.2f}x faster than {r.engine} ({r.name})")

    # Show sample outputs for quality validation
    outputs_shown = False
    for r in sorted_results:
        if r.sample_output:
            if not outputs_shown:
                print(f"\n{'='*80}")
                print("SAMPLE OUTPUTS (for quality validation)")
                print(f"{'='*80}")
                outputs_shown = True
            print(f"\n[{r.engine}] {r.name}:")
            sample = r.sample_output[:200]
            if len(r.sample_output) > 200:
                sample += "..."
            print(f"  {sample}")


def cmd_ollama(args) -> int:
    """Run Ollama benchmark."""
    runner = OllamaRunner(
        model_name=args.model,
        host=args.host,
        verbose=not args.quiet,
    )

    result = runner.run(
        prompt=args.prompt,
        max_tokens=args.tokens,
        iterations=args.iterations,
        warmup=not args.no_warmup,
    )

    print_result(result)

    if args.json:
        print(json.dumps(result.__dict__, indent=2))

    return 0 if result.error is None else 1


def cmd_transformers(args) -> int:
    """Run Transformers benchmark."""
    runner = TransformersRunner(
        model_name=args.model,
        device=args.device,
        quantize=args.quant,
        torch_dtype=args.dtype,
        verbose=not args.quiet,
    )

    result = runner.run(
        prompt=args.prompt,
        max_tokens=args.tokens,
        iterations=args.iterations,
        warmup=not args.no_warmup,
    )

    print_result(result)

    if args.json:
        print(json.dumps(result.__dict__, indent=2))

    return 0 if result.error is None else 1


def cmd_vllm(args) -> int:
    """Run vLLM benchmark."""
    runner = VLLMRunner(
        model_name=args.model,
        quantization=args.quant,
        tensor_parallel_size=args.tp,
        gpu_memory_utilization=args.gpu_mem,
        dtype=args.dtype,
        verbose=not args.quiet,
    )

    result = runner.run(
        prompt=args.prompt,
        max_tokens=args.tokens,
        iterations=args.iterations,
        warmup=not args.no_warmup,
    )

    print_result(result)

    if args.json:
        print(json.dumps(result.__dict__, indent=2))

    return 0 if result.error is None else 1


def cmd_webllm(args) -> int:
    """Run WebLLM benchmark."""
    runner = WebLLMRunner(
        model_name=args.model,
        headless=not args.head,
        verbose=not args.quiet,
    )

    result = runner.run(
        prompt=args.prompt,
        max_tokens=args.tokens,
        iterations=args.iterations,
        warmup=not args.no_warmup,
    )

    print_result(result)

    if args.json:
        print(json.dumps(result.__dict__, indent=2))

    return 0 if result.error is None else 1


def cmd_doppler(args) -> int:
    """Run Doppler benchmark."""
    runner = DopplerRunner(
        model_name=args.model,
        doppler_path=args.doppler_path,
        kernel_profile=args.kernel_profile,
        headed=args.head,
        verbose=not args.quiet,
    )

    result = runner.run(
        prompt=args.prompt,
        max_tokens=args.tokens,
        iterations=args.iterations,
        warmup=not args.no_warmup,
    )

    print_result(result)

    if args.json:
        print(json.dumps(result.__dict__, indent=2))

    return 0 if result.error is None else 1


def cmd_compare(args) -> int:
    """Compare multiple engines."""
    import time as time_module

    results = []

    prompt = args.prompt
    tokens = args.tokens
    iterations = args.iterations
    warmup = not args.no_warmup
    cooldown = args.cooldown

    def do_cooldown(label: str = ""):
        """Wait for GPU to cool down between benchmarks."""
        if cooldown > 0 and results:  # Skip before first benchmark
            print(f"\nCooling down for {cooldown}s{' after ' + label if label else ''}...")
            time_module.sleep(cooldown)

    # Run Ollama benchmarks
    for model in args.ollama or []:
        do_cooldown(results[-1].name if results else "")
        runner = OllamaRunner(model_name=model, verbose=not args.quiet)
        result = runner.run(prompt=prompt, max_tokens=tokens, iterations=iterations, warmup=warmup)
        results.append(result)

    # Run Transformers benchmarks
    for spec in args.hf or []:
        do_cooldown(results[-1].name if results else "")
        # Parse model:quant format
        if ":" in spec and "/" not in spec.split(":")[0]:
            # Format: quant:model (e.g., int4:openai/gpt-oss-20b)
            quant, model = spec.split(":", 1)
        elif spec.count(":") > 1:
            # Format: model:quant (e.g., openai/gpt-oss-20b:int4)
            parts = spec.rsplit(":", 1)
            model, quant = parts[0], parts[1]
        else:
            model, quant = spec, None

        runner = TransformersRunner(
            model_name=model,
            device=args.device,
            quantize=quant,
            torch_dtype=args.dtype,
            verbose=not args.quiet,
        )
        result = runner.run(prompt=prompt, max_tokens=tokens, iterations=iterations, warmup=warmup)
        results.append(result)

    # Run vLLM benchmarks
    for spec in args.vllm or []:
        do_cooldown(results[-1].name if results else "")
        # Parse model:quant format
        if spec.count(":") > 1:
            parts = spec.rsplit(":", 1)
            model, quant = parts[0], parts[1]
        else:
            model, quant = spec, None

        runner = VLLMRunner(
            model_name=model,
            quantization=quant,
            tensor_parallel_size=args.tp,
            gpu_memory_utilization=args.gpu_mem,
            dtype=args.dtype,
            verbose=not args.quiet,
        )
        result = runner.run(prompt=prompt, max_tokens=tokens, iterations=iterations, warmup=warmup)
        results.append(result)

    # Run WebLLM benchmarks
    for model in args.webllm or []:
        do_cooldown(results[-1].name if results else "")
        runner = WebLLMRunner(model_name=model, headless=True, verbose=not args.quiet)
        result = runner.run(prompt=prompt, max_tokens=tokens, iterations=iterations, warmup=warmup)
        results.append(result)

    # Run Doppler benchmarks
    for model in args.doppler or []:
        do_cooldown(results[-1].name if results else "")
        runner = DopplerRunner(
            model_name=model,
            doppler_path=getattr(args, "doppler_path", None),
            kernel_profile=getattr(args, "kernel_profile", "fast"),
            headed=False,
            verbose=not args.quiet,
        )
        result = runner.run(prompt=prompt, max_tokens=tokens, iterations=iterations, warmup=warmup)
        results.append(result)

    # Print comparison
    if results:
        print_comparison(results)

        if args.json:
            print(json.dumps([r.__dict__ for r in results], indent=2))

    return 0 if all(r.error is None for r in results) else 1


def main():
    parser = argparse.ArgumentParser(
        description="Benchmark inference engines",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # Common args
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--prompt", type=str, default="Write a short story about a robot learning to paint.",
                        help="Prompt for generation")
    common.add_argument("--tokens", type=int, default=100, help="Max tokens to generate (default: 100)")
    common.add_argument("--iterations", type=int, default=3, help="Benchmark iterations (default: 3)")
    common.add_argument("--no-warmup", action="store_true", help="Skip warmup run")
    common.add_argument("--quiet", "-q", action="store_true", help="Reduce output verbosity")
    common.add_argument("--json", action="store_true", help="Output results as JSON")

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Ollama subcommand
    p_ollama = subparsers.add_parser("ollama", parents=[common], help="Benchmark Ollama model")
    p_ollama.add_argument("model", help="Ollama model name (e.g., gpt-oss:20b)")
    p_ollama.add_argument("--host", default="http://localhost:11434", help="Ollama host URL")
    p_ollama.set_defaults(func=cmd_ollama)

    # Transformers subcommand
    p_hf = subparsers.add_parser("transformers", aliases=["hf"], parents=[common],
                                  help="Benchmark HuggingFace Transformers model")
    p_hf.add_argument("model", help="HuggingFace model name (e.g., openai/gpt-oss-20b)")
    p_hf.add_argument("--quant", choices=["int4", "nf4", "fp4", "int8", None], default=None,
                      help="Quantization method (bitsandbytes)")
    p_hf.add_argument("--dtype", choices=["fp16", "bf16", "fp32"], default="bf16",
                      help="Torch dtype (default: bf16)")
    p_hf.add_argument("--device", default="auto", help="Device (auto, cuda, cpu)")
    p_hf.set_defaults(func=cmd_transformers)

    # vLLM subcommand
    p_vllm = subparsers.add_parser("vllm", parents=[common], help="Benchmark vLLM model")
    p_vllm.add_argument("model", help="Model name (e.g., openai/gpt-oss-20b)")
    p_vllm.add_argument("--quant", choices=["awq", "gptq", "squeezellm", "fp8", None], default=None,
                        help="Quantization method")
    p_vllm.add_argument("--dtype", default="auto", help="Data type (auto, float16, bfloat16)")
    p_vllm.add_argument("--tp", type=int, default=1, help="Tensor parallel size (default: 1)")
    p_vllm.add_argument("--gpu-mem", type=float, default=0.9, help="GPU memory utilization (default: 0.9)")
    p_vllm.set_defaults(func=cmd_vllm)

    # WebLLM subcommand
    p_webllm = subparsers.add_parser("webllm", parents=[common], help="Benchmark WebLLM model (browser WebGPU)")
    p_webllm.add_argument("model", help="Model name (e.g., llama-3.2-1b, gemma-2-2b, qwen2-1.5b)")
    p_webllm.add_argument("--head", action="store_true", help="Show browser window (default: headless)")
    p_webllm.set_defaults(func=cmd_webllm)

    # Doppler subcommand
    p_doppler = subparsers.add_parser("doppler", parents=[common], help="Benchmark Doppler WebGPU engine")
    p_doppler.add_argument("model", help="Model name (e.g., gemma-3-1b, gemma-2-2b, llama-3.2-1b)")
    p_doppler.add_argument("--doppler-path", type=str, default=None,
                           help="Path to doppler repo (default: ../ouroboros/doppler)")
    p_doppler.add_argument("--kernel-profile", "-k", choices=["fast", "safe", "debug", "fused", "apple"],
                           default="fast", help="Kernel profile (default: fast)")
    p_doppler.add_argument("--head", action="store_true", help="Show browser window (default: headless)")
    p_doppler.set_defaults(func=cmd_doppler)

    # Compare subcommand
    p_compare = subparsers.add_parser("compare", parents=[common], help="Compare multiple engines")
    p_compare.add_argument("--ollama", nargs="+", metavar="MODEL", help="Ollama models to benchmark")
    p_compare.add_argument("--hf", nargs="+", metavar="MODEL[:QUANT]",
                           help="HuggingFace models (optionally with :quant suffix)")
    p_compare.add_argument("--vllm", nargs="+", metavar="MODEL[:QUANT]",
                           help="vLLM models (optionally with :quant suffix)")
    p_compare.add_argument("--webllm", nargs="+", metavar="MODEL",
                           help="WebLLM models (e.g., llama-3.2-1b, gemma-2-2b)")
    p_compare.add_argument("--doppler", nargs="+", metavar="MODEL",
                           help="Doppler models (e.g., gemma-3-1b, gemma-2-2b)")
    p_compare.add_argument("--doppler-path", type=str, default=None,
                           help="Path to doppler repo")
    p_compare.add_argument("--kernel-profile", "-k", default="fast",
                           help="Doppler kernel profile (default: fast)")
    p_compare.add_argument("--dtype", default="bf16", help="Default dtype for HF/vLLM")
    p_compare.add_argument("--device", default="auto", help="Device for HF models")
    p_compare.add_argument("--tp", type=int, default=1, help="Tensor parallel size for vLLM")
    p_compare.add_argument("--gpu-mem", type=float, default=0.9, help="GPU memory utilization for vLLM")
    p_compare.add_argument("--cooldown", type=int, default=0,
                           help="Seconds to wait between benchmarks for GPU to cool (default: 0)")
    p_compare.set_defaults(func=cmd_compare)

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        return 1

    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
