#!/usr/bin/env python3
"""Reprice frozen QM5 causal spans on the compact final-P1 trace."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

import fractal3_shortest_unique_trigger_qm5 as qm5


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "fractal3_compact_shortest_unique_transfer_qc0_v1"
OUTPUT_DIR = ROOT / "results" / CANDIDATE_ID
TRACE = ROOT / "results/fractal2_compact_trace_10m_v1/compact.p1"
TRACE_RECEIPT = ROOT / "results/fractal2_compact_trace_10m_v1/decision.json"
ENDPOINT_QM5 = ROOT / "results/fractal3_shortest_unique_trigger_qm5_v1/decision.json"


def artifact(path: Path) -> dict[str, object]:
    data = path.read_bytes()
    return {
        "path": str(path.relative_to(ROOT)),
        "bytes": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
    }


def main() -> int:
    if not TRACE_RECEIPT.is_file():
        raise SystemExit(f"missing compact trace receipt: {TRACE_RECEIPT}")
    trace_receipt = json.loads(TRACE_RECEIPT.read_text())
    if not trace_receipt["proof"]["archive_identity"]:
        raise SystemExit("compact trace archive identity did not pass")
    if any(not guard["memory_clean"] for guard in trace_receipt["guards"].values()):
        raise SystemExit("compact trace memory proof did not pass")

    endpoint = json.loads(ENDPOINT_QM5.read_text())
    endpoint_j0 = float(endpoint["arms"]["J0"]["displaced_bytes"])
    qm5.CANDIDATE_ID = CANDIDATE_ID
    if "--parent-p1" not in sys.argv:
        sys.argv.extend(("--parent-p1", str(TRACE)))
    if "--output-dir" not in sys.argv:
        sys.argv.extend(("--output-dir", str(OUTPUT_DIR)))
    status = qm5.main()
    if status != 0:
        return status

    output = OUTPUT_DIR / "decision.json"
    row = json.loads(output.read_text())
    compact_j0 = float(row["arms"]["J0"]["displaced_bytes"])
    uplift = compact_j0 - endpoint_j0
    if uplift < 10_000:
        row["failed_conditions"].append(
            "compact_uplift_over_endpoint428_qm5_below_10000_bytes"
        )
    row["schema"] = "enwiki9_fractal3_compact_shortest_unique_transfer_qc0_v1"
    row["inputs"]["compact_trace_receipt"] = artifact(TRACE_RECEIPT)
    row["inputs"]["endpoint428_qm5_decision"] = artifact(ENDPOINT_QM5)
    row["diagnostics"] = {
        "endpoint428_qm5_J0_displaced_bytes": endpoint_j0,
        "compact_J0_displaced_bytes": compact_j0,
        "compact_uplift_over_endpoint428_qm5_bytes": uplift,
    }
    row["contracts"] = {
        "qm5_causal_span_universe_frozen": True,
        "compact_trace_archive_identity": True,
        "compact_source_bound_forecast_bytes": 109_499_618,
        "target_bytes": 105_000_000,
        "compact_forecast_debt_bytes": 4_499_618,
        "paid_compact_net_gate_bytes_at_10m": 60_000,
    }
    row["verdict"] = (
        "promote_to_paid_compact_replay"
        if not row["failed_conditions"]
        else "retire_compact_shortest_unique_transfer"
    )
    row["claim_boundary"] = (
        "Exact archive-identical compact-parent repricing of frozen decoder-causal "
        "QM5 spans. Rule definitions, source identities, and invocations remain "
        "free; this gate earns zero score credit and cannot change the forecast."
    )
    temporary = output.with_suffix(".json.rewrite.tmp")
    temporary.write_text(json.dumps(row, indent=2, sort_keys=True) + "\n")
    temporary.replace(output)
    print(json.dumps({
        "candidate_id": CANDIDATE_ID,
        "J0_displaced_bytes": compact_j0,
        "uplift_bytes": uplift,
        "failed_conditions": row["failed_conditions"],
        "verdict": row["verdict"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
