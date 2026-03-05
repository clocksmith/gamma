#!/usr/bin/env python3
"""GAMMA - Unified CLI entry point."""

from __future__ import annotations

import argparse
import os
import sys
import warnings

from src.core.cli_help import print_command_help, print_main_help
from src.core.cli_router import TOP_LEVEL_COMMANDS, route_command


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
SRC_DIR = os.path.join(ROOT_DIR, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)


def main() -> None:
    if len(sys.argv) == 1 or (len(sys.argv) == 2 and sys.argv[1] in ["-h", "--help"]):
        print_main_help()
        sys.exit(0)

    if sys.argv[1] == "help":
        if len(sys.argv) > 2:
            print_command_help(sys.argv[2])
        else:
            print_main_help()
        sys.exit(0)

    parser = argparse.ArgumentParser(
        description="GAMMA - LLM Research Framework",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        add_help=False,
    )
    parser.add_argument(
        "command",
        nargs="?",
        default="game",
        choices=TOP_LEVEL_COMMANDS,
        help="Command to run (default: game)",
    )
    args, remaining_args = parser.parse_known_args()
    route_command(args.command, remaining_args, ROOT_DIR, print_command_help)


if __name__ == "__main__":
    main()
