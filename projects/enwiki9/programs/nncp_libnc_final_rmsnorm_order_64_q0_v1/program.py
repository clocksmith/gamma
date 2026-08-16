#!/usr/bin/env python3
"""Descriptor for the production final-RMSNorm operation-order oracle."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RUNNER = ROOT / "tools/nncp_libnc_final_rmsnorm_order_64_q0.py"
