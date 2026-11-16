#!/usr/bin/env python3
"""Compatibility launcher for gamma.commands.benchmark_model_speed."""

try:
    from tools._path_setup import ensure_project_root_on_path
except ImportError:
    from _path_setup import ensure_project_root_on_path

ensure_project_root_on_path()

from gamma.commands.benchmark_model_speed import main

if __name__ == "__main__":
    main()
