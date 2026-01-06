#!/usr/bin/env python3
"""
GAMMA - Unified CLI Entry Point

Main entry point for all GAMMA experiments, benchmarks, and tools:
- game: Interactive LLM prediction game
- mind-meld: Multi-model collaboration experiments
- comparison: Side-by-side model comparison
- benchmark: Speed & performance benchmarking
- dream: DREAM benchmark suite (mind meld + language benchmarks)
- select: Interactive engine/model selector

Usage:
    gamma.py game [options]           # Interactive game (default)
    gamma.py mind-meld [options]      # Mind meld experiments
    gamma.py comparison [options]     # Model comparison
    gamma.py benchmark [options]      # Speed benchmarking
    gamma.py dream [options]          # DREAM benchmarks
    gamma.py select                   # Interactive engine selector
"""

import argparse
import sys
import os
import warnings

warnings.filterwarnings(
    "ignore",
    message=r".*torch_dtype.*deprecated.*",
    category=UserWarning,
)
warnings.filterwarnings(
    "ignore",
    message=r".*torch_dtype.*deprecated.*",
    category=FutureWarning,
)
warnings.filterwarnings(
    "ignore",
    message=r".*np\.object.*",
    category=FutureWarning,
    module=r"keras\.src\.export\.tf2onnx_lib",
)

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.join(ROOT_DIR, 'src')
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)


def print_main_help():
    """Print main help message with better organization."""
    help_text = """
╔══════════════════════════════════════════════════════════════════════╗
║                  GAMMA - LLM Research Framework                      ║
║          Unified platform for model experiments & benchmarks         ║
╚══════════════════════════════════════════════════════════════════════╝

USAGE:
  gamma.py [command] [options]

COMMANDS:

  game              Interactive LLM prediction game (default)
  comparison        Side-by-side model comparison
  mind-meld         Multi-model collaboration experiments
  benchmark         Speed & performance benchmarking
  dream             DREAM benchmark suite
  list              List all available models
  select            Interactive engine & model selector
  help              Show detailed help for a specific command

═══════════════════════════════════════════════════════════════════════

QUICK START EXAMPLES:

  # Interactive game mode
  gamma.py game --model pytorch:google/gemma-2-2b-it

  # Compare two models side-by-side
  gamma.py comparison \\
    --models pytorch:google/gemma-2-2b-it ollama:qwen2:7b

  # Mind meld two models with pattern-based swapping
  gamma.py mind-meld \\
    --models pytorch:google/gemma-2-2b-it pytorch:Qwen/Qwen2-7B-Instruct \\
    --strategy pattern --steps 30

  # Benchmark model speed
  gamma.py benchmark \\
    --models pytorch:google/gemma-2-2b-it vllm:google/gemma-2-7b-it \\
    --tokens 100 --iterations 5

  # Interactive engine selector (get recommendations)
  gamma.py select

  # DREAM mind meld benchmarks
  gamma.py dream mind-meld --models MODEL1 MODEL2

═══════════════════════════════════════════════════════════════════════

DOCUMENTATION:
  • Project overview:       README.md
  • Engine details:         src/engines/README.md
  • Docs index:             docs/README.md

NEED HELP?
  • Detailed help:          gamma.py help [command]
  • List models:            gamma.py benchmark --list-models
  • Engine selector:        gamma.py select
  • GitHub issues:          https://github.com/anthropics/gamma/issues

═══════════════════════════════════════════════════════════════════════
"""
    print(help_text)


def print_command_help(command):
    """Print detailed help for a specific command."""
    helps = {
        'game': """
GAMMA Game Mode - Interactive LLM Prediction

Visualize model predictions, attention weights, and probability distributions
in real-time as you guide the model's generation.

USAGE:
  gamma.py game [options]

OPTIONS:
  --model ENGINE:MODEL       Model to use (default: pytorch:google/gemma-2-2b-it)
  --engine ENGINE            Engine type (pytorch, ollama, vllm, etc.)
  --chat                     Chat mode for conversations
  --temperature FLOAT        Sampling temperature (default: 0.7)
  --top-k INT                Top-K sampling (default: 8)
  --top-p FLOAT              Top-P (nucleus) sampling (default: 0.95)
  --steps INT                Max generation steps
  --verbose                  Show detailed information

EXAMPLES:
  # Basic game mode
  gamma.py game

  # Use specific model
  gamma.py game --model vllm:google/gemma-2-7b-it

  # Chat mode with Ollama model
  gamma.py game --chat --model ollama:qwen2:7b

See also: gamma.py comparison, gamma.py mind-meld
        """,

        'comparison': """
GAMMA Comparison Mode - Side-by-Side Model Comparison

Compare two models running the same prompt with synchronized visualization
of their predictions, attention, and probability distributions.

USAGE:
  gamma.py comparison --models ENGINE:MODEL1 ENGINE:MODEL2 [options]

REQUIRED:
  --models MODEL1 MODEL2     Two models to compare (engine:model format)

OPTIONS:
  --temperature FLOAT        Sampling temperature (default: 0.7)
  --top-k INT                Top-K sampling (default: 8)
  --top-p FLOAT              Top-P (nucleus) sampling (default: 0.95)
  --steps INT                Max generation steps
  --verbose                  Show detailed information

EXAMPLES:
  # Compare PyTorch vs Ollama
  gamma.py comparison \\
    --models pytorch:google/gemma-2-2b-it ollama:qwen2:7b

  # Compare same model, different engines
  gamma.py comparison \\
    --models pytorch:google/gemma-2-2b-it vllm:google/gemma-2-2b-it

  # Compare different sizes
  gamma.py comparison \\
    --models pytorch:google/gemma-2-2b-it pytorch:google/gemma-2-9b-it

NOTE: Both models must support the chosen engine format.

See also: gamma.py game, gamma.py benchmark
        """,

        'mind-meld': """
GAMMA Mind Meld - Multi-Model Collaboration

Merge multiple models using various swap strategies. Models take turns or
collaborate based on confidence, perplexity, or other criteria.

USAGE:
  gamma.py mind-meld --models ENGINE:MODEL1 ENGINE:MODEL2 [options]

REQUIRED:
  --models MODEL1 MODEL2 ... Two or more models (engine:model format)

SWAP STRATEGIES:
  --strategy pattern         Swap at punctuation marks (., !, ?)
  --strategy fixed           Swap every N tokens (use --fixed-interval)
  --strategy round_robin     Alternate models each token
  --strategy perplexity      Swap when model is uncertain
  --strategy confidence      Swap when confidence drops
  --strategy random          Random swapping

ENSEMBLE OPTIONS:
  --use-weighted-average     Blend all model probabilities
  --use-abe                  Agreement-Based Ensembling
  --use-blending             Blend logits instead of swapping

OTHER OPTIONS:
  --fixed-interval INT       Token interval for fixed strategy (default: 3)
  --temperature FLOAT        Sampling temperature
  --top-k INT                Top-K sampling
  --top-p FLOAT              Top-P sampling
  --steps INT                Number of generation steps
  --prompt TEXT              Initial prompt
  --verbose                  Detailed output

EXAMPLES:
  # Pattern-based swapping (swap at punctuation)
  gamma.py mind-meld \\
    --models pytorch:google/gemma-2-2b-it pytorch:Qwen/Qwen2-7B-Instruct \\
    --strategy pattern --steps 30

  # Perplexity-based swapping (swap when uncertain)
  gamma.py mind-meld \\
    --models pytorch:google/gemma-2-2b-it pytorch:google/gemma-2-9b-it \\
    --strategy perplexity --steps 40

  # Weighted averaging (blend all models)
  gamma.py mind-meld \\
    --models pytorch:google/gemma-2-2b-it pytorch:Qwen/Qwen2-7B-Instruct \\
    --use-weighted-average --steps 30

  # Three models with round-robin
  gamma.py mind-meld \\
    --models \\
      pytorch:google/gemma-2-2b-it \\
      pytorch:Qwen/Qwen2-7B-Instruct \\
      vllm:meta-llama/Llama-2-7b-chat-hf \\
    --strategy round_robin --steps 50

☡  IMPORTANT: Mind melding requires engines with logits access!
   ✓ Use: pytorch, pytorch_cuda, vllm, llamacpp, mlx, mlx_gpu
   ✗ DON'T use: ollama (no logits via HTTP API)

See also: gamma.py benchmark, gamma.py dream
        """,

        'benchmark': """
GAMMA Benchmark - Speed & Performance Testing

Measure tokens per second, latency, and compare performance across
different engines and models.

USAGE:
  gamma.py benchmark --models ENGINE:MODEL1 [ENGINE:MODEL2 ...] [options]

REQUIRED:
  --models MODEL1 [MODEL2 ...]  One or more models to benchmark

OPTIONS:
  --tokens INT               Tokens to generate per iteration (default: 50)
  --iterations INT           Number of iterations (default: 3)
  --save                     Save results to JSON file
  --list-models              List available models and exit

EXAMPLES:
  # Benchmark single model
  gamma.py benchmark \\
    --models pytorch:google/gemma-2-2b-it \\
    --tokens 100 --iterations 5

  # Compare multiple engines for same model
  gamma.py benchmark \\
    --models \\
      pytorch:google/gemma-2-2b-it \\
      vllm:google/gemma-2-2b-it \\
      llamacpp:./models/gemma-2-2b-q4.gguf \\
    --tokens 100 --iterations 5

  # Compare different models
  gamma.py benchmark \\
    --models \\
      pytorch:google/gemma-2-2b-it \\
      pytorch:google/gemma-2-9b-it \\
      pytorch:google/gemma-2-27b-it \\
    --tokens 50 --iterations 3

  # List available models
  gamma.py benchmark --list-models

OUTPUT:
  • Tokens per second (tok/s)
  • Latency per token (ms)
  • Total time
  • Success rate
  • Speedup comparisons

See also: docs/BENCHMARKING.md, gamma.py dream
        """,

        'dream': """
GAMMA DREAM Benchmarks - Comprehensive Evaluation Suite

Run DREAM (Dynamic Research for Evolving AI Models) benchmarks including:
- Mind meld performance benchmarks
- Language comparison (TypeScript vs JavaScript)
- Model capability evaluations

USAGE:
  gamma.py dream [benchmark-type] [options]

BENCHMARK TYPES:
  mind-meld             Mind meld benchmarking suite
  language              Language comparison (TS vs JS)
  all                   Run all DREAM benchmarks

MIND MELD BENCHMARKS:
  gamma.py dream mind-meld \\
    --models MODEL1 MODEL2 \\
    --strategies pattern fixed perplexity \\
    --output results.json

LANGUAGE BENCHMARKS:
  gamma.py dream language [options]

  KEY OPTIONS (Dimension-based API):
    -c, --category <name>       Category or group (foundations, backend, ui, ...)
    -t, --task <name>           Specific task name
    -p, --provider <name>       Provider (ollama-gpt-oss-20b, openai-gpt4, ...)
    -l, --language <lang>       Languages to test (js, ts, jsdoc, all, or comma-separated)
    --prompt-level <level>      Prompt quality levels (novice, beginner, intermediate,
                                 advanced, expert, all, or comma-separated)
    --all-prompt-levels         All 5 prompt levels (novice through expert)
    --temperature <n>           LLM sampling temperature (0.0-2.0, default 1.0)
                                 Use 0.0 for deterministic, higher for variation
    --runs <n>                  Number of runs per variant (default: 1)
    --help                      Show full language benchmark help

  PROMPT QUALITY LEVELS:
    Each task can be tested with 5 instruction clarity levels:
    • novice       - Minimal instruction ("make fibonacci")
    • beginner     - Basic instruction ("create a fibonacci function")
    • intermediate - Moderate detail ("write a function to calculate fibonacci")
    • advanced     - Specific with function names and parameters
    • expert       - Complete detailed instructions with language-specific requirements

  TEMPERATURE CONTROL:
    • 0.0  = Deterministic (identical outputs across runs)
    • 1.0  = Default (good variation for testing code diversity)
    • 1.5+ = Maximum creativity (more unpredictable outputs)

EXAMPLES:
  # Run mind meld benchmarks
  gamma.py dream mind-meld \\
    --models pytorch:google/gemma-2-2b-it pytorch:Qwen/Qwen2-7B-Instruct

  # Test JS vs TS, all prompt levels, 5 runs each
  gamma.py dream language \\
    --category foundations \\
    --language js,ts \\
    --all-prompt-levels \\
    --provider ollama-qwen3-30b \\
    --runs 5

  # Test prompt effectiveness: novice vs expert comparison
  gamma.py dream language \\
    --category foundations \\
    --language js \\
    --prompt-level novice,expert \\
    --provider ollama-gpt-oss-20b \\
    --runs 3

  # High temperature for code variation analysis
  gamma.py dream language \\
    --category foundations \\
    --language ts \\
    --temperature 1.0 \\
    --provider ollama-qwen3-30b \\
    --runs 5

  # Deterministic testing (zero temperature, reproducible results)
  gamma.py dream language \\
    --category foundations \\
    --language js,ts \\
    --prompt-level expert \\
    --temperature 0.0 \\
    --provider ollama-gpt-oss-120b \\
    --runs 3

  # Use mock responses for testing (dry mode)
  gamma.py dream language \\
    --task fibonacci \\
    --language js,ts \\
    --dry

  # Legacy API still works (variant strings)
  gamma.py dream language \\
    --task fibonacci \\
    --variant javascript-expert,typescript-expert \\
    --provider ollama-qwen3-30b \\
    --runs 5

  # Full DREAM suite
  gamma.py dream all --output results/

See also: src/benchmarks/dream/README.md
        """,

        'list': """
GAMMA List Models - Show Available Models

List all available models from all sources:
- Ollama models (via ollama list)
- HuggingFace cached models (~/.cache/huggingface/hub)
- Local GGUF files (models directory and Ollama blobs)

USAGE:
  gamma.py list

EXAMPLES:
  # List all models
  gamma.py list

OUTPUT:
  Shows models organized by source:
  • Ollama models with sizes and modification dates
  • HuggingFace cached models with total cache size
  • Local GGUF files with file sizes
  • Quick reference for using models

Use this command to discover what models you have before running
benchmarks, comparisons, or mind meld experiments.

See also: gamma.py benchmark --list-models, gamma.py select
        """,

        'select': """
GAMMA Engine Selector - Interactive Tool

Interactive tool to help choose the right engine for your model,
hardware, and use case.

USAGE:
  gamma.py select [MODEL]

FEATURES:
  • Hardware detection (CUDA, Apple Silicon, CPU)
  • Model format detection (GGUF, HuggingFace, ONNX)
  • Use case recommendations (speed, mind meld, research, production)
  • Model specification validation
  • Example command generation

EXAMPLES:
  # Interactive mode
  gamma.py select

  # Quick recommendation for specific model
  gamma.py select google/gemma-2-2b-it

  # Validate a model specification
  gamma.py select --validate pytorch:google/gemma-2-2b-it

OPTIONS:
  MODEL                  Optional model to get recommendations for
  --validate SPEC        Validate an engine:model specification

See also: docs/ENGINE_ARCHITECTURE.md, docs/QUICK_START_ENGINES.md
        """
    }

    if command in helps:
        print(helps[command])
    else:
        print(f"No detailed help available for '{command}'")
        print(f"Try: gamma.py {command} --help")


def main():
    # Check for help command or no args
    if len(sys.argv) == 1:
        print_main_help()
        sys.exit(0)

    if len(sys.argv) == 2 and sys.argv[1] in ['-h', '--help']:
        print_main_help()
        sys.exit(0)

    # Check for 'help' command
    if sys.argv[1] == 'help':
        if len(sys.argv) > 2:
            print_command_help(sys.argv[2])
        else:
            print_main_help()
        sys.exit(0)

    parser = argparse.ArgumentParser(
        description='GAMMA - LLM Research Framework',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        add_help=False,
    )

    parser.add_argument(
        'command',
        nargs='?',
        default='game',
        choices=['game', 'mind-meld', 'comparison', 'benchmark', 'dream', 'list', 'select', 'help'],
        help='Command to run (default: game)'
    )

    # Parse just the command, let the specific tool handle the rest
    args, remaining_args = parser.parse_known_args()

    # Route to the appropriate command
    if args.command == 'game':
        from src.game.cli import main as game_main
        sys.argv = ['gamma.py'] + remaining_args
        game_main()

    elif args.command == 'mind-meld':
        from tools.run_mind_meld_cli import main as mind_meld_main
        sys.argv = ['run_mind_meld_cli.py'] + remaining_args
        mind_meld_main()

    elif args.command == 'comparison':
        from src.game.cli import main as game_main
        sys.argv = ['gamma.py', '--comparison'] + remaining_args
        game_main()

    elif args.command == 'benchmark':
        from tools.benchmark_model_speed import main as benchmark_main
        sys.argv = ['benchmark_model_speed.py'] + remaining_args
        benchmark_main()

    elif args.command == 'dream':
        # Route to DREAM benchmarks
        if len(remaining_args) == 0 or remaining_args[0] in ['-h', '--help']:
            print_command_help('dream')
            sys.exit(0)

        dream_type = remaining_args[0] if remaining_args else 'mind-meld'

        if dream_type == 'mind-meld':
            # Run mind meld benchmarks
            from src.benchmarks.mind_meld_benchmark import main as dream_mm_main
            sys.argv = ['mind_meld_benchmark.py'] + remaining_args[1:]
            dream_mm_main()

        elif dream_type == 'language':
            # Run language comparison benchmarks (Node.js)
            benchmark_dir = os.path.join(ROOT_DIR, 'src', 'benchmarks', 'dream')
            if not os.path.exists(benchmark_dir):
                print(f"Error: DREAM benchmarks not found at {benchmark_dir}")
                sys.exit(1)

            print("Running DREAM language comparison benchmarks (Node.js)...")
            print(f"  Working directory: {benchmark_dir}\n")

            import subprocess
            cmd = ['node', 'index.js'] + remaining_args[1:]
            try:
                result = subprocess.run(cmd, cwd=benchmark_dir)
                sys.exit(result.returncode)
            except FileNotFoundError:
                print("Error: Node.js not found. Install from https://nodejs.org/")
                sys.exit(1)
            except Exception as e:
                print(f"Error running benchmark: {e}")
                sys.exit(1)

        elif dream_type == 'all':
            print("Running all DREAM benchmarks...")
            print("\n" + "="*70)
            print("1/2 - Mind Meld Benchmarks")
            print("="*70)
            from src.benchmarks.mind_meld_benchmark import main as dream_mm_main
            sys.argv = ['mind_meld_benchmark.py'] + remaining_args[1:]
            dream_mm_main()

            print("\n" + "="*70)
            print("2/2 - Language Comparison Benchmarks")
            print("="*70)
            benchmark_dir = os.path.join(ROOT_DIR, 'src', 'benchmarks', 'dream')
            import subprocess
            subprocess.run(['node', 'index.js'] + remaining_args[1:], cwd=benchmark_dir)

        else:
            print(f"Unknown DREAM benchmark type: {dream_type}")
            print("Available types: mind-meld, language, all")
            print_command_help('dream')
            sys.exit(1)

    elif args.command == 'list':
        # List available models
        from tools.list_models import main as list_main
        sys.argv = ['list_models.py'] + remaining_args
        list_main()

    elif args.command == 'select':
        # Run engine selector
        from tools.engine_selector import main as selector_main
        sys.argv = ['engine_selector.py'] + remaining_args
        selector_main()

    elif args.command == 'help':
        if remaining_args:
            print_command_help(remaining_args[0])
        else:
            print_main_help()
        sys.exit(0)


if __name__ == '__main__':
    main()
