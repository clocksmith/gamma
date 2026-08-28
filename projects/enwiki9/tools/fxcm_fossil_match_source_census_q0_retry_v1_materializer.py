#!/usr/bin/env python3
"""Declare the implementation-only bindings for the FOSSIL census retry."""

from pathlib import Path


PROJECT = Path(__file__).resolve().parents[1]
RUNNER = PROJECT / "tools/fxcm_fossil_match_source_census_q0_retry_v1.py"
COMPILER = Path("/usr/bin/x86_64-linux-gnu-g++-15")


def main() -> int:
    if not RUNNER.is_file() or not COMPILER.is_file() or COMPILER.is_symlink():
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
