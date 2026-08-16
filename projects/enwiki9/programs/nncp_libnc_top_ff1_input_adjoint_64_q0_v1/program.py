#!/usr/bin/env python3
"""Descriptor for the production top-FF1 input-adjoint oracle."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RUNNER = ROOT / "tools/nncp_libnc_top_ff1_input_adjoint_64_q0_v1.py"
