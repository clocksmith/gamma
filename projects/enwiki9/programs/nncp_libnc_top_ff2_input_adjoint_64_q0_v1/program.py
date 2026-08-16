#!/usr/bin/env python3
"""Descriptor for the production top-layer FF2-input adjoint capture."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RUNNER = ROOT / (
    "tools/nncp_libnc_top_ff2_input_adjoint_64_q0_v1.py"
)
