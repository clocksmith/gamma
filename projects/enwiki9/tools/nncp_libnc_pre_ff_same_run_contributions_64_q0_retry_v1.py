#!/usr/bin/env python3
"""Retry the same-run contribution oracle with corrected antecedents."""

from __future__ import annotations

from pathlib import Path

import nncp_libnc_pre_ff_same_run_contributions_64_q0_v1 as parent


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "nncp_libnc_pre_ff_same_run_contributions_64_q0_retry_v1"
RESULT = ROOT / "results" / CANDIDATE_ID
RUNNER = Path(__file__).resolve()
MATERIALIZER = ROOT / (
    "tools/nncp_libnc_pre_ff_same_run_contributions_64_q0_retry_v1_materializer.py"
)
PROGRAM_DESCRIPTOR = ROOT / "programs" / CANDIDATE_ID / "program.py"


def main() -> int:
    parent.CANDIDATE_ID = CANDIDATE_ID
    parent.RESULT = RESULT
    parent.WORK = RESULT / "work"
    parent.RUNNER = RUNNER
    parent.MATERIALIZER = MATERIALIZER
    parent.PROGRAM_DESCRIPTOR = PROGRAM_DESCRIPTOR
    return parent.main()


if __name__ == "__main__":
    raise SystemExit(main())
