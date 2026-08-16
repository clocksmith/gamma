#!/usr/bin/env python3
"""Descriptor for the declaration-order repair of the attention oracle."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RUNNER = ROOT / (
    "tools/nncp_libnc_top_attention_product_oracle_64_q0_retry_v1.py"
)
