#!/usr/bin/env python3
"""Descriptor for receipt-only salvage of the top attention oracle."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RUNNER = ROOT / (
    "tools/nncp_libnc_top_attention_product_oracle_64_q0_retry_v2.py"
)
