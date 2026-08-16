#!/usr/bin/env python3
"""Descriptor for the open top-layer FF1 bias projection gate."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RUNNER = ROOT / (
    "tools/nncp_open_profile_top_ff1_bias_gradient_64_q0_retry_v2.py"
)
