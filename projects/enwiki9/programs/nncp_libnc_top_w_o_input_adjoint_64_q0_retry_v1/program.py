#!/usr/bin/env python3
"""Descriptor for receipt-only salvage of the layer-19 w_o oracle."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RUNNER = ROOT / "tools/nncp_libnc_top_w_o_input_adjoint_64_q0_retry_v1.py"
