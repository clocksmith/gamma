#!/usr/bin/env python3
"""Descriptor for the state-reduced layer-19 pre-FF backward."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RUNNER = ROOT / (
    "tools/nncp_open_top_pre_ff_rmsnorm_backward_state_reduce_64_q0.py"
)
