#!/usr/bin/env python3
"""Descriptor for the zero-credit production-profile GGML parity gate.

The executable gate is ``tools/nncp_ggml_profile_forward_parity_64_qm10.py``.
It extracts one receipt-bound LibNC oracle fixture, builds the static CPU-only
fixed-shape GGML forward, compares every frozen layer checkpoint and arithmetic
branch path, and never exposes the fixture as a codec runtime dependency.
"""
