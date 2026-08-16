#!/usr/bin/env python3
"""Descriptor for the BF16 gain-product final RMSNorm retry."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RUNNER = ROOT / "tools/nncp_open_profile_final_norm_backward_64_q0_retry_v2.py"
