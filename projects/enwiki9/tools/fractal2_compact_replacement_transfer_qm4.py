#!/usr/bin/env python3
"""Rejected tombstone for the noncausal compact QM3 transfer."""

from __future__ import annotations

import json
from pathlib import Path
import sys

import fractal2_recursive_punct_forest_qm2 as qm2


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "fractal2_compact_replacement_transfer_qm4_v1"
OUTPUT = ROOT / f"results/{CANDIDATE_ID}/decision.json"
TRACE = ROOT / "results/fractal2_compact_trace_10m_v1/compact.p1"
TRACE_RECEIPT = ROOT / "results/fractal2_compact_trace_10m_v1/decision.json"
ENDPOINT_QM3 = ROOT / "results/fractal2_endpoint428_recursive_punct_qm3_v1/decision.json"


def main() -> int:
    raise SystemExit(
        "retired: QM3 opportunities are not decoder-derived; use a separately "
        "frozen causal compact-transfer proposal"
    )
    # Kept below as an auditable record of the never-executed proposal.
    if not TRACE_RECEIPT.is_file():
        raise SystemExit(f"missing archive-identity receipt: {TRACE_RECEIPT}")
    trace_receipt = json.loads(TRACE_RECEIPT.read_text())
    if not trace_receipt["proof"]["archive_identity"]:
        raise SystemExit("compact trace archive identity did not pass")

    qm2.CANDIDATE_ID = CANDIDATE_ID
    qm2.QM1_DECISION = ENDPOINT_QM3
    if "--parent-p1" not in sys.argv:
        sys.argv.extend(("--parent-p1", str(TRACE)))
    if "--output" not in sys.argv:
        sys.argv.extend(("--output", str(OUTPUT)))
    status = qm2.main()
    if status != 0:
        return status

    row = json.loads(OUTPUT.read_text())
    row["schema"] = "fractal2_compact_replacement_transfer_qm4_gate_minus1_v1"
    row["candidate_id"] = CANDIDATE_ID
    row["inputs"]["endpoint428_qm3_decision"] = row["inputs"].pop(
        "qm1_decision"
    )
    row["inputs"]["compact_trace_receipt"] = qm2.qm1.artifact(TRACE_RECEIPT)
    row["diagnostic_displaced_delta_vs_endpoint428_qm3_bytes"] = row.pop(
        "incremental_J0_over_QM1_bytes"
    )
    row["contracts"]["qm3_rule_universe_frozen"] = True
    row["contracts"]["compact_trace_archive_identity"] = True
    row["contracts"]["compact_source_bound_forecast_bytes"] = 109_499_618
    row["contracts"]["target_bytes"] = 105_000_000
    row["contracts"]["compact_forecast_debt_bytes"] = 4_499_618
    row["decision"]["paid_compact_net_gate_bytes_at_10m"] = 60_000
    row["claim_boundary"] = (
        "Exact archive-identical compact-replacement Gate -1 repricing of the "
        "frozen QM3 universe. Rule and source identities remain free. This is "
        "zero-credit and cannot change the forecast or authorize native code "
        "unless every frozen gate passes and a separate paid replay retains "
        "at least 60000 net bytes."
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
