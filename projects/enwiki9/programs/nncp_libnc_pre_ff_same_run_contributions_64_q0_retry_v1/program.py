#!/usr/bin/env python3
"""Descriptor for the corrected same-run contribution oracle."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RUNNER = ROOT / (
    "tools/nncp_libnc_pre_ff_same_run_contributions_64_q0_retry_v1.py"
)
