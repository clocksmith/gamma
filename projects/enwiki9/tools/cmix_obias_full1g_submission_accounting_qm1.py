#!/usr/bin/env python3
"""Correct only the frozen source-decision byte count in accounting q0."""

from __future__ import annotations

import json

import cmix_obias_full1g_submission_accounting_qm0 as base


CANDIDATE_ID = "cmix_obias_full1g_submission_accounting_qm1_v1"
PARENT_DECISION_SHA256 = "b90849237a47e7aea625b192dc0748773df090bcde3a053eaf3594a47b534966"


def main() -> int:
    parent_decision = base.RESULT / "decision.json"
    if base.sha256(parent_decision) != PARENT_DECISION_SHA256:
        raise ValueError("q0 accounting decision identity mismatch")
    source_hash = base.EXPECTED[base.SOURCE_DECISION][1]
    base.EXPECTED = dict(base.EXPECTED)
    base.EXPECTED[base.SOURCE_DECISION] = (45_242, source_hash)
    base.CANDIDATE_ID = CANDIDATE_ID
    base.RESULT = base.ROOT / "results" / CANDIDATE_ID
    returncode = base.main()

    decision_path = base.RESULT / "decision.json"
    decision = json.loads(decision_path.read_text())
    decision["schema"] = "enwiki9_cmix_obias_full1g_submission_accounting_qm1_v1"
    decision["parent_decision_sha256"] = PARENT_DECISION_SHA256
    decision["fixture_correction"] = "source_decision_bytes_6790_to_45242"
    decision_path.write_text(json.dumps(decision, indent=2, sort_keys=True) + "\n")
    print(json.dumps(decision, indent=2, sort_keys=True))
    return returncode


if __name__ == "__main__":
    raise SystemExit(main())
