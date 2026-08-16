#!/usr/bin/env python3
"""Descriptor for the corrected production full-update oracle fixture."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RUNNER = ROOT / "tools/nncp_libnc_profile_update_fixture_64_q1.py"
