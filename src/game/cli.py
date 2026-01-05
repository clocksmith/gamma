#!/usr/bin/env python3
"""
Legacy CLI entry point.

This module forwards to the package entrypoint in src.game.cli.main.
"""

from src.game.cli.main import main


if __name__ == "__main__":
    main()
