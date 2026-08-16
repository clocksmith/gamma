#!/usr/bin/env python3
"""Descriptor for the F32-injected LibNC gradient-merge retry."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RUNNER = ROOT / "tools/nncp_libnc_bf16_gradient_merge_64_q0_retry_v5.py"
