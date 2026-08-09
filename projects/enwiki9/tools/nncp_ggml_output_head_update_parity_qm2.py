#!/usr/bin/env python3
"""Run GGML head parity with a completed two-copy accumulation period."""

from __future__ import annotations

import json

import nncp_ggml_output_head_update_parity_qm0 as base


CANDIDATE_ID = "nncp_ggml_output_head_update_parity_qm2_v1"
Q0_DECISION_SHA256 = "172871eaf9e940e1f08c5368933d8cb89e3dd5a4952fd24a08563b3bdf8c4a36"
Q1_GUARD_SHA256 = "29e58a09b409ea184f40b03ba15fb7bc38fb225a0bdc0939b6a2dea2d3e22d26"


def main() -> int:
    q0_decision = base.RESULT / "decision.json"
    q1_guard = base.common.ROOT / "results/nncp_ggml_output_head_update_parity_qm1_guard_v1.json"
    if base.common.sha256(q0_decision) != Q0_DECISION_SHA256:
        raise ValueError("q0 decision identity mismatch")
    if base.common.sha256(q1_guard) != Q1_GUARD_SHA256:
        raise ValueError("q1 guard identity mismatch")

    base.CANDIDATE_ID = CANDIDATE_ID
    base.PROGRAM = base.common.ROOT / "programs" / CANDIDATE_ID
    base.RESULT = base.common.ROOT / "results" / CANDIDATE_ID
    returncode = base.main()

    decision_path = base.RESULT / "decision.json"
    decision = json.loads(decision_path.read_text())
    decision["schema"] = "enwiki9_nncp_ggml_output_head_update_parity_qm2_v1"
    decision["q0_decision_sha256"] = Q0_DECISION_SHA256
    decision["q1_guard_sha256"] = Q1_GUARD_SHA256
    decision["normalization_change"] = "two_identical_batches_complete_opt_period_2"
    decision_path.write_text(json.dumps(decision, indent=2, sort_keys=True) + "\n")
    print(json.dumps(decision, indent=2, sort_keys=True))
    return returncode


if __name__ == "__main__":
    raise SystemExit(main())
