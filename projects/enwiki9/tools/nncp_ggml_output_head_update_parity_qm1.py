#!/usr/bin/env python3
"""Run the one-physical-batch correction of GGML output-head parity."""

from __future__ import annotations

import json

import nncp_ggml_output_head_update_parity_qm0 as parent


CANDIDATE_ID = "nncp_ggml_output_head_update_parity_qm1_v1"
PARENT_DECISION_SHA256 = "172871eaf9e940e1f08c5368933d8cb89e3dd5a4952fd24a08563b3bdf8c4a36"


def main() -> int:
    parent_decision = parent.RESULT / "decision.json"
    if parent.common.sha256(parent_decision) != PARENT_DECISION_SHA256:
        raise ValueError("q0 parent decision identity mismatch")

    parent.CANDIDATE_ID = CANDIDATE_ID
    parent.PROGRAM = parent.common.ROOT / "programs" / CANDIDATE_ID
    parent.RESULT = parent.common.ROOT / "results" / CANDIDATE_ID
    returncode = parent.main()

    decision_path = parent.RESULT / "decision.json"
    decision = json.loads(decision_path.read_text())
    decision["schema"] = "enwiki9_nncp_ggml_output_head_update_parity_qm1_v1"
    decision["parent_decision_sha256"] = PARENT_DECISION_SHA256
    decision["normalization_change"] = "ggml_opt_period_2_to_1"
    decision_path.write_text(json.dumps(decision, indent=2, sort_keys=True) + "\n")
    print(json.dumps(decision, indent=2, sort_keys=True))
    return returncode


if __name__ == "__main__":
    raise SystemExit(main())
