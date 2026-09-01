#!/usr/bin/env python3
"""Validation-only materializer for the Fiber-FOSSIL v5 envelope."""

from __future__ import annotations

import argparse
from pathlib import Path
import subprocess
import sys


PROJECT = Path(__file__).resolve().parents[1]
RUNNER = PROJECT / "tools/wiki_fiber_fossil_endpoint428_opening1m_q0_v6.py"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--snapshot-root", type=Path, required=True)
    arguments = parser.parse_args()
    completed = subprocess.run(
        [
            sys.executable,
            str(RUNNER),
            "--validate-only",
            "--snapshot-root",
            str(arguments.snapshot_root.resolve()),
        ],
        cwd=PROJECT,
        check=False,
    )
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
