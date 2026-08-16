#!/usr/bin/env python3
"""Identify the unchanged exact-forward program for comparator retry."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROGRAM = ROOT / "programs/nncp_ggml_postupdate_forward_parity_64_q1_retry_v1"

