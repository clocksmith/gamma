#!/usr/bin/env python3
"""
Flux - Interactive Diffusion Model Learning Lab

Main CLI entry point for all Flux features.
"""

import sys
import argparse
import logging

sys.path.insert(0, '/home/clocksmith/deco/gamma-core')
from gamma_core.ui import print_header, print_separator, color_text, UIConfig
from gamma_core.game import GameSession, DifficultyLevel

from src.engines.base import DiffusionConfig
from src.engines.diffusers_engine import DiffusersEngine
from src.games.reconstruction import ReconstructionGame
from src.games.playground import ParameterPlayground
from src.games.comparison_game import ComparisonGame


def setup_logging(verbose: bool):
    """Setup logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )


def print_welcome():
    """Print welcome message."""
    print_header("🌊 Welcome to Flux")
    print(f"\n{color_text('Interactive Diffusion Model Learning Lab', UIConfig.COLOR_CYAN)}")
    print(f"\nLearn how stable diffusion works through hands-on games!")
    print_separator()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Flux - Interactive Diffusion Model Learning Lab",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Launch main menu
  python flux.py

  # Play reconstruction game
  python flux.py reconstruction --prompt "A mountain landscape"

  # Open parameter playground
  python flux.py playground --prompt "A futuristic city"

  # Use specific model
  python flux.py --model stabilityai/stable-diffusion-xl-base-1.0 reconstruction

Learning Modes:
  reconstruction    Learn denoising through image reconstruction challenge
  playground        Explore parameter effects interactively
        """
    )

    # Global options
    parser.add_argument(
        "--model",
        type=str,
        default="stabilityai/stable-diffusion-2-1-base",
        help="Model name or path (default: SD 2.1)"
    )
    parser.add_argument(
        "--difficulty",
        type=str,
        choices=["simple", "learner", "explorer", "researcher"],
        default="learner",
        help="Difficulty level (default: learner)"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    parser.add_argument(
        "--device",
        type=str,
        choices=["auto", "cpu", "cuda", "mps"],
        default="auto",
        help="Device to use (default: auto-detect)"
    )

    # Subcommands
    subparsers = parser.add_subparsers(dest="mode", help="Learning mode")

    # Reconstruction game
    recon_parser = subparsers.add_parser(
        "reconstruction",
        help="Image reconstruction challenge"
    )
    recon_parser.add_argument(
        "--prompt",
        type=str,
        help="Text prompt (random if not specified)"
    )
    recon_parser.add_argument(
        "--rounds",
        type=int,
        default=1,
        help="Number of rounds to play (default: 1)"
    )
    recon_parser.add_argument(
        "--steps",
        type=int,
        default=50,
        help="Number of diffusion steps (default: 50)"
    )

    # Parameter playground
    play_parser = subparsers.add_parser(
        "playground",
        help="Parameter tuning playground"
    )
    play_parser.add_argument(
        "--prompt",
        type=str,
        required=True,
        help="Text prompt to experiment with"
    )
    play_parser.add_argument(
        "--guidance",
        type=float,
        default=7.5,
        help="Initial guidance scale (default: 7.5)"
    )
    play_parser.add_argument(
        "--steps",
        type=int,
        default=50,
        help="Initial number of steps (default: 50)"
    )
    play_parser.add_argument(
        "--scheduler",
        type=str,
        default="pndm",
        help="Initial scheduler (default: pndm)"
    )

    # Model comparison
    comp_parser = subparsers.add_parser(
        "compare",
        help="Multi-model comparison"
    )
    comp_parser.add_argument(
        "--models",
        nargs="+",
        help="Model paths to compare"
    )
    comp_parser.add_argument(
        "--prompt",
        type=str,
        help="Text prompt (interactive if not specified)"
    )

    args = parser.parse_args()

    # Setup
    setup_logging(args.verbose)

    # Show welcome
    if not args.mode:
        print_welcome()

    # Map difficulty string to enum
    difficulty_map = {
        "simple": DifficultyLevel.SIMPLE,
        "learner": DifficultyLevel.LEARNER,
        "explorer": DifficultyLevel.EXPLORER,
        "researcher": DifficultyLevel.RESEARCHER,
    }
    difficulty = difficulty_map[args.difficulty]

    # Create engine configuration
    config = DiffusionConfig(
        model_name=args.model,
        num_inference_steps=getattr(args, "steps", 50),
        device_map=args.device if args.device != "auto" else "auto",
    )

    # Initialize engine
    print(f"\n{color_text('🔧 Initializing...', UIConfig.COLOR_YELLOW)}")
    print(f"   Model: {args.model}")
    print(f"   Difficulty: {difficulty.get_display_name()}")

    engine = DiffusersEngine(config)

    try:
        engine.load()

        # Route to appropriate mode
        if args.mode == "reconstruction":
            # Create game session
            session = GameSession(
                session_id="reconstruction",
                current_level=difficulty
            )

            # Launch reconstruction game
            game = ReconstructionGame(engine, session)
            game.play(
                prompt=args.prompt,
                num_rounds=args.rounds
            )

        elif args.mode == "playground":
            # Launch parameter playground
            playground = ParameterPlayground(engine)
            playground.explore(
                prompt=args.prompt,
                initial_guidance_scale=args.guidance,
                initial_steps=args.steps,
                initial_scheduler=args.scheduler,
            )

        elif args.mode == "compare":
            # Multi-model comparison (doesn't use single engine)
            engine.unload()  # Unload the default engine

            session = GameSession(
                session_id="comparison",
                current_level=difficulty
            )

            game = ComparisonGame(session)
            game.play(
                model_paths=args.models,
                prompt=args.prompt
            )

        else:
            # Interactive menu
            show_menu(engine, difficulty)

    except KeyboardInterrupt:
        print(f"\n\n{color_text('Interrupted by user', UIConfig.COLOR_WARNING)}")
    except Exception as e:
        print(f"\n{color_text(f'Error: {e}', UIConfig.COLOR_ERROR)}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)
    finally:
        # Cleanup
        print(f"\n{color_text('🧹 Cleaning up...', UIConfig.COLOR_YELLOW)}")
        engine.unload()

    print(f"\n{color_text('Thanks for using Flux!', UIConfig.COLOR_SUCCESS)}")


def show_menu(engine: DiffusersEngine, difficulty: DifficultyLevel):
    """Show interactive menu."""
    print(f"\n{color_text('Choose a learning mode:', UIConfig.COLOR_CYAN)}")
    print_separator()
    print("  [1] Image Reconstruction Challenge")
    print("      Watch noise transform into images, predict the result")
    print()
    print("  [2] Parameter Tuning Playground")
    print("      Experiment with guidance scale, steps, schedulers")
    print()
    print("  [3] Multi-Model Comparison")
    print("      Compare different diffusion models side-by-side")
    print()
    print("  [q] Quit")
    print_separator()

    choice = input(f"\n{color_text('Choose [1-3]:', UIConfig.COLOR_PROMPT)} ").strip()

    if choice == "1":
        session = GameSession(session_id="reconstruction", current_level=difficulty)
        game = ReconstructionGame(engine, session)
        game.play()

    elif choice == "2":
        prompt = input(f"\n{color_text('Enter prompt:', UIConfig.COLOR_PROMPT)} ").strip()
        if prompt:
            playground = ParameterPlayground(engine)
            playground.explore(prompt)
        else:
            print(color_text("No prompt provided, returning to menu", UIConfig.COLOR_WARNING))

    elif choice == "3":
        # Unload current engine
        engine.unload()

        # Launch comparison
        session = GameSession(session_id="comparison", current_level=difficulty)
        game = ComparisonGame(session)
        game.play()

    elif choice == "q":
        pass

    else:
        print(color_text("Invalid choice", UIConfig.COLOR_ERROR))


if __name__ == "__main__":
    main()
