#!/usr/bin/env python3
"""Descriptor for the first post-update production-profile forward gate."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RUNNER = ROOT / "tools/nncp_ggml_postupdate_forward_parity_64_q1_retry_v1.py"
