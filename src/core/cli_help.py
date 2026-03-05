"""Top-level CLI help text for the GAMMA entrypoint."""

from __future__ import annotations


MAIN_HELP_TEXT = """
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
  codegen           Code generation benchmarks (TS vs JS)
  list              List all available models
  select            Interactive engine & model selector
  help              Show detailed help for a specific command

═══════════════════════════════════════════════════════════════════════

QUICK START EXAMPLES:

  # Interactive game mode
  gamma.py game --model pytorch:google/gemma-2-2b-it

  # Compare two models side-by-side
  gamma.py comparison \
    --models pytorch:google/gemma-2-2b-it ollama:qwen2:7b

  # Mind meld two models with pattern-based swapping
  gamma.py mind-meld \
    --models pytorch:google/gemma-2-2b-it pytorch:Qwen/Qwen2-7B-Instruct \
    --strategy pattern --steps 30

  # Benchmark model speed
  gamma.py benchmark \
    --models pytorch:google/gemma-2-2b-it vllm:google/gemma-2-7b-it \
    --tokens 100 --iterations 5

  # Interactive engine selector (get recommendations)
  gamma.py select

  # Codegen mind meld benchmarks
  gamma.py codegen mind-meld --models MODEL1 MODEL2

═══════════════════════════════════════════════════════════════════════

DOCUMENTATION:
  • Project overview:       README.md
  • Architecture map:       docs/ARCHITECTURE.md
  • Engine details:         src/engines/README.md
  • Docs index:             docs/README.md

NEED HELP?
  • Detailed help:          gamma.py help [command]
  • List models:            gamma.py benchmark --list-models
  • Engine selector:        gamma.py select
  • GitHub issues:          https://github.com/anthropics/gamma/issues

═══════════════════════════════════════════════════════════════════════
"""


COMMAND_HELPS = {
    "game": """
GAMMA Game Mode - Interactive LLM Prediction

USAGE:
  gamma.py game [options]

See also: gamma.py comparison, gamma.py mind-meld
    """,
    "comparison": """
GAMMA Comparison Mode - Side-by-Side Model Comparison

USAGE:
  gamma.py comparison --models ENGINE:MODEL1 ENGINE:MODEL2 [options]

See also: gamma.py game, gamma.py benchmark
    """,
    "mind-meld": """
GAMMA Mind Meld - Multi-Model Collaboration

USAGE:
  gamma.py mind-meld --models ENGINE:MODEL1 ENGINE:MODEL2 [options]

☡  IMPORTANT: Mind melding requires engines with logits access.

See also: gamma.py benchmark, gamma.py codegen
    """,
    "benchmark": """
GAMMA Benchmark - Speed & Performance Testing

USAGE:
  gamma.py benchmark --models ENGINE:MODEL1 [ENGINE:MODEL2 ...] [options]

See also: docs/BENCHMARKING.md, gamma.py codegen
    """,
    "codegen": """
GAMMA Codegen Benchmarks - TS/JS Prompt Ladder Benchmarks

USAGE:
  gamma.py codegen [benchmark-type] [options]

BENCHMARK TYPES:
  mind-meld             Mind meld benchmarking suite
  language              Language comparison (TS vs JS)
  all                   Run all codegen benchmarks

See also: tools/codegen-bench/README.md
    """,
    "list": """
GAMMA List Models - Show Available Models

USAGE:
  gamma.py list

See also: gamma.py benchmark --list-models, gamma.py select
    """,
    "select": """
GAMMA Engine Selector - Interactive Tool

USAGE:
  gamma.py select [MODEL]

See also: docs/ENGINE_ARCHITECTURE.md, docs/ARCHITECTURE.md
    """,
}


def print_main_help() -> None:
    print(MAIN_HELP_TEXT)


def print_command_help(command: str) -> None:
    text = COMMAND_HELPS.get(command)
    if text is None:
        print(f"No detailed help available for '{command}'")
        print(f"Try: gamma.py {command} --help")
        return
    print(text)

