#!/usr/bin/env python3
"""Descriptor for the BF16-upstream top-layer FF2 gradient retry."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RUNNER = ROOT / "tools/nncp_open_profile_top_ff2_gradient_64_q0_retry_v1.py"
