#!/usr/bin/env python3
"""Descriptor for the exact open production-profile memory transition."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RUNNER = ROOT / "tools/nncp_ggml_profile_memory_transition_64_q0.py"
