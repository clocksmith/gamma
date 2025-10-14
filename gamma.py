#!/usr/bin/env python3
"""
GAMMA - Unified CLI Entry Point

Main entry point for all GAMMA tools:
- game: Interactive LLM prediction game
- mind-meld: Multi-model collaboration experiments
- comparison: Side-by-side model comparison
- benchmark: LLM performance testing
- language-comparison: TypeScript vs JavaScript benchmarking (from DREAM)

Usage:
    gamma.py game [options]              # Interactive game (default)
    gamma.py mind-meld [options]         # Mind meld experiments
    gamma.py comparison [options]        # Model comparison
    gamma.py benchmark [options]         # Python benchmarks
    gamma.py language-comparison [opts]  # JS/TS benchmarks (Node.js)

For backward compatibility, game.py still exists and works as before.
"""

import argparse
import sys
import os

def main():
    parser = argparse.ArgumentParser(
        description='GAMMA - LLM Exploration and Comparison Toolkit',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Tools:
  game                Interactive LLM prediction game
  mind-meld           Multi-model collaboration experiments
  comparison          Side-by-side model comparison
  benchmark           Performance testing (Python)
  language-comparison TypeScript vs JavaScript benchmarking (Node.js)

Examples:
  gamma.py game --chat
  gamma.py comparison --models ollama:qwen3:30b pytorch:google/gemma-2-2b-it
  gamma.py mind-meld --strategy round_robin
  gamma.py language-comparison --task fibonacci

For more help on a specific tool:
  gamma.py game --help
  gamma.py mind-meld --help
        """
    )

    parser.add_argument(
        'tool',
        nargs='?',
        default='game',
        choices=['game', 'mind-meld', 'comparison', 'benchmark', 'language-comparison'],
        help='Tool to run (default: game)'
    )

    # Parse just the tool name, let the specific tool handle the rest
    args, remaining_args = parser.parse_known_args()

    # Route to the appropriate tool
    if args.tool == 'game':
        # Import and run the game
        from game import main as game_main
        sys.argv = ['game.py'] + remaining_args
        game_main()

    elif args.tool == 'mind-meld':
        # Import and run mind meld CLI
        from tools.run_mind_meld_cli import main as mind_meld_main
        sys.argv = ['run_mind_meld_cli.py'] + remaining_args
        mind_meld_main()

    elif args.tool == 'comparison':
        # Run comparison mode via game.py with --comparison flag
        from game import main as game_main
        sys.argv = ['game.py', '--comparison'] + remaining_args
        game_main()

    elif args.tool == 'benchmark':
        print("Python benchmarks:")
        print("  - Mind Meld: Run 'gamma.py mind-meld --benchmark'")
        print("  - General: See src/benchmarks/ for available benchmarks")
        sys.exit(0)

    elif args.tool == 'language-comparison':
        # Run the Node.js benchmark suite
        benchmark_dir = os.path.join(os.path.dirname(__file__), 'src', 'benchmarks', 'language_comparison')
        if not os.path.exists(benchmark_dir):
            print(f"Error: Language comparison benchmark not found at {benchmark_dir}")
            sys.exit(1)

        print("Running language comparison benchmarks (Node.js)...")
        print(f"  Working directory: {benchmark_dir}")
        print()

        import subprocess
        cmd = ['node', 'index.js'] + remaining_args
        try:
            result = subprocess.run(cmd, cwd=benchmark_dir)
            sys.exit(result.returncode)
        except FileNotFoundError:
            print("Error: Node.js not found. Please install Node.js to run language comparison benchmarks.")
            print("  Visit: https://nodejs.org/")
            sys.exit(1)
        except Exception as e:
            print(f"Error running benchmark: {e}")
            sys.exit(1)

if __name__ == '__main__':
    main()
