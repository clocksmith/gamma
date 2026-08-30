#!/usr/bin/env python3
"""Retry HORIZON-DUALCLOCK with static identity-buffer storage only."""

from pathlib import Path

import endpoint428_horizon_dualclock_source_census_q0_v2 as parent


PROJECT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "endpoint428_horizon_dualclock_source_census_q0_retry_v1"


def main() -> int:
    parent.CANDIDATE_ID = CANDIDATE_ID
    parent.RESULT = PROJECT / "results" / CANDIDATE_ID
    parent.CANDIDATE = PROJECT / "programs" / CANDIDATE_ID
    parent.SOURCE = parent.CANDIDATE / "horizon-dualclock-scan.cpp"
    parent.SCAN_SCHEMA = parent.CANDIDATE / "scan-receipt.schema.json"
    parent.EXPERIMENT = (
        PROJECT / "operations/adaptive/experiments" / f"{CANDIDATE_ID}.json"
    )
    parent.SOURCE_SHA256 = (
        "ff08edea191055ceecc23ebf6008e1aaa2f0f573c1a005b61d6a48c45be68b8a"
    )
    parent.SCAN_SCHEMA_SHA256 = (
        "5db9b62cff338ac34b2da7c5d72b7d4fc0bf4828b55671489162e424f0c04610"
    )
    return parent.main()


if __name__ == "__main__":
    raise SystemExit(main())
