#!/usr/bin/env python3
"""Declare the implementation-only bindings for the dual-clock retry."""

from pathlib import Path


PROJECT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "endpoint428_horizon_dualclock_source_census_q0_retry_v1"
RUNNER = PROJECT / "tools" / f"{CANDIDATE_ID}.py"
SOURCE = PROJECT / "programs" / CANDIDATE_ID / "horizon-dualclock-scan.cpp"
SCHEMA = PROJECT / "programs" / CANDIDATE_ID / "scan-receipt.schema.json"
COMPILER = Path("/usr/bin/x86_64-linux-gnu-g++-15")


def main() -> int:
    required = (RUNNER, SOURCE, SCHEMA, COMPILER)
    if any(not path.is_file() for path in required) or COMPILER.is_symlink():
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
