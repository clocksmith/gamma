#!/usr/bin/env python3
"""Run frozen FRACTAL-2 QM2 on the archive-identical Endpoint428 10M trace."""

from __future__ import annotations

import json
from pathlib import Path
import sys

import fractal2_recursive_punct_forest_qm2 as qm2


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "fractal2_endpoint428_recursive_punct_qm3_v1"
OUTPUT = ROOT / f"results/{CANDIDATE_ID}/decision.json"
TRACE = ROOT / "results/fractal2_endpoint428_trace_10m_v1/endpoint428.p1"
TRACE_RECEIPT = ROOT / "results/fractal2_endpoint428_trace_10m_v1/decision.json"
WRONG_PARENT_QM2 = ROOT / "results/fractal2_recursive_punct_forest_qm2_v1/decision.json"


def main() -> int:
    qm2.CANDIDATE_ID = CANDIDATE_ID
    qm2.QM1_DECISION = WRONG_PARENT_QM2
    if "--parent-p1" not in sys.argv:
        sys.argv.extend(("--parent-p1", str(TRACE)))
    if "--output" not in sys.argv:
        sys.argv.extend(("--output", str(OUTPUT)))
    status = qm2.main()
    if status != 0:
        return status
    row = json.loads(OUTPUT.read_text())
    row["schema"] = "fractal2_endpoint428_recursive_punct_qm3_gate_minus1_v1"
    row["candidate_id"] = CANDIDATE_ID
    row["inputs"]["wrong_parent_qm2_decision"] = row["inputs"].pop("qm1_decision")
    row["inputs"]["endpoint428_trace_receipt"] = qm2.qm1.artifact(TRACE_RECEIPT)
    row["diagnostic_comparison_to_wrong_parent_qm2_bytes"] = row.pop(
        "incremental_J0_over_QM1_bytes"
    )
    row["contracts"]["wrong_parent_comparison_not_promotable"] = True
    row["contracts"]["archive_identical_endpoint428_trace"] = True
    row["claim_boundary"] = (
        "Exact archive-identical Endpoint428 Gate -1 repricing with free rule and "
        "source identities. It is zero-credit and does not serialize a codec. "
        "The QM2 numeric comparison uses a different parent and is diagnostic only."
    )
    temporary = OUTPUT.with_suffix(".json.rewrite.tmp")
    temporary.write_text(json.dumps(row, indent=2, sort_keys=True) + "\n")
    temporary.replace(OUTPUT)
    print(
        json.dumps(
            {
                "candidate_id": CANDIDATE_ID,
                "J0_displaced_bytes": row["arms"]["J0"]["displaced_bytes"],
                "margins": row["J0_control_margins_bytes"],
                "verdict": row["decision"]["verdict"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
