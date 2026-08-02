#!/usr/bin/env python3
"""Adaptive-workflow entry point for the SRSTC Gate-minus-one oracle."""

from pathlib import Path
import runpy


TOOL = Path(__file__).resolve().parents[2] / "tools/srstc_residual_program_ceiling.py"
runpy.run_path(str(TOOL), run_name="__main__")
