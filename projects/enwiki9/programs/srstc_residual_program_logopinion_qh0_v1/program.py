#!/usr/bin/env python3
"""Adaptive-workflow entry point for SRSTC log-opinion QH0."""

from pathlib import Path
import runpy


TOOL = Path(__file__).resolve().parents[2] / "tools/srstc_residual_program_logopinion.py"
runpy.run_path(str(TOOL), run_name="__main__")
