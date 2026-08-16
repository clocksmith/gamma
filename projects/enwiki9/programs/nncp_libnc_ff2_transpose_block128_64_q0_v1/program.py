#!/usr/bin/env python3
"""Descriptor for production FF2-transpose 128-panel attribution."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RUNNER = ROOT / "tools/nncp_libnc_ff2_transpose_block128_64_q0.py"
