#!/usr/bin/env python3
"""Descriptor for the open layer-19 w_o gradient slice."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RUNNER = ROOT / "tools/nncp_open_w_o_weight_slice_post_add_64_q0.py"
